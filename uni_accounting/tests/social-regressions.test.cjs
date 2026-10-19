const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const { parse } = require('@vue/compiler-sfc');
const { ref, reactive, computed, nextTick } = require('vue');

// 直接运行页面脚本；只替换平台接口和计时器，不连接后端。
function loadPage(path, names, api = {}) {
  const filename = resolve(__dirname, '../src/pages', path);
  const { descriptor, errors } = parse(readFileSync(filename, 'utf8'));
  assert.equal(errors.length, 0);
  const timers = new Map();
  let timerId = 0;
  let unload = () => {};
  let confirm;
  const context = {
    ref, reactive, computed, nextTick, console,
    onLoad() {}, onShow() {}, onMounted() {},
    onUnload(callback) { unload = callback; },
    setTimeout(callback) { timers.set(++timerId, callback); return timerId; },
    clearTimeout(id) { timers.delete(id); },
    uni: {
      navigateBack() {}, showToast() {},
      getStorageSync: () => ({ user_info: { userId: 1 } }),
      showModal(options) { confirm = () => options.success({ confirm: true }); },
    },
    ...api,
  };
  const script = descriptor.scriptSetup.content.replace(/^import .*;\s*$/gm, '');
  vm.runInNewContext(`${script}\nthis.page = { ${names.join(', ')} };`, context, { filename });
  return {
    ...context.page, timers,
    unload: () => unload(),
    confirm: () => confirm(),
    flushTimers() {
      for (const [id, callback] of timers) {
        timers.delete(id);
        callback();
      }
    },
  };
}

function chatPage() {
  return loadPage('discover/page_chatroom/chatroom.vue', [
    'chatList', 'messages', 'inputText', 'scrollTarget', 'openChat', 'backToList', 'sendMessage',
  ]);
}

function send(page, index = 0) {
  page.openChat(page.chatList.value[index]);
  page.inputText.value = '测试消息';
  page.sendMessage();
}

test('发送后返回列表，模拟回复仍归属原会话且不报错', async () => {
  const page = chatPage();
  send(page);
  page.backToList();
  page.scrollTarget.value = 'unchanged';
  page.flushTimers();
  await nextTick();
  assert.equal(page.messages.value[1].length, 2);
  assert.equal(page.messages.value[1][1].isMe, false);
  assert.equal(page.scrollTarget.value, 'unchanged');
});

test('快速切换会话，不串消息也不滚动当前会话', async () => {
  const page = chatPage();
  send(page);
  const before = page.messages.value[2].length;
  page.openChat(page.chatList.value[1]);
  await nextTick();
  page.scrollTarget.value = 'unchanged';
  page.flushTimers();
  await nextTick();
  assert.equal(page.messages.value[1].length, 2);
  assert.equal(page.messages.value[2].length, before);
  assert.equal(page.scrollTarget.value, 'unchanged');
});

test('连续发送的模拟回复各自回到发送时的会话', () => {
  const page = chatPage();
  const before = page.messages.value[2].length;
  send(page);
  send(page, 1);
  page.flushTimers();
  assert.equal(page.messages.value[1].length, 2);
  assert.equal(page.messages.value[2].length, before + 2);
  assert.equal(page.timers.size, 0);
});

test('页面卸载清理所有模拟回复和待处理滚动', async () => {
  const page = chatPage();
  send(page);
  send(page);
  page.unload();
  page.scrollTarget.value = 'unchanged';
  assert.equal(page.timers.size, 0);
  page.flushTimers();
  await nextTick();
  assert.equal(page.messages.value[1].length, 2);
  assert.equal(page.scrollTarget.value, 'unchanged');
});

function postData(deleted = false) {
  const child = { id: 2, authorId: 2, root_id: deleted ? null : 1, reply_to: '原作者' };
  const root = deleted ? { ...child, child_comments: [] }
    : { id: 1, authorId: 1, root_id: null, child_comments: [child] };
  return { postId: 1, comments: deleted ? 1 : 2, realComments: [root], likes: 0, isLiked: false };
}

test('社区删除评论后更新回复目标，保留展开状态和待同步的点赞', async () => {
  let deleted = false;
  let submitted;
  const page = loadPage('discover/community.vue', [
    'posts', 'fetchPosts', 'handleDelete', 'showReplyInput', 'replyContent', 'submitReply',
  ], {
    getPostList: async () => ({ code: 0, data: [postData(deleted)] }),
    deleteComment: async () => { deleted = true; return { code: 0 }; },
    publishComment: async data => { submitted = data; return { code: 0 }; },
  });
  await page.fetchPosts();
  const post = page.posts.value[0];
  post.visibleCommentCount = 5;
  post.isLiked = true;
  post.likes = 1;
  page.showReplyInput(1, post.flattenedComments[1]);
  page.replyContent.value = '继续回复';
  page.handleDelete('comment', post, post.flattenedComments[0]);
  await page.confirm();
  const updated = page.posts.value[0];
  assert.equal(updated.visibleCommentCount, 5);
  assert.equal(updated.comments, 1);
  assert.equal(updated.flattenedComments[0].root_id, null);
  assert.equal(updated.isLiked, true);
  assert.equal(updated.likes, 1);
  await page.submitReply(1);
  assert.equal(submitted.parent_id, 2);
  assert.equal(submitted.root_id, 2);
  assert.equal(submitted.reply_to_id, 2);
});

test('删除正在回复的评论时关闭输入框，防止向已删除对象提交', async () => {
  let deleted = false;
  const page = loadPage('discover/community.vue', [
    'posts', 'fetchPosts', 'handleDelete', 'showReplyInput', 'replyPost', 'replyComment',
  ], {
    getPostList: async () => ({ code: 0, data: [postData(deleted)] }),
    deleteComment: async () => { deleted = true; return { code: 0 }; },
  });
  await page.fetchPosts();
  const post = page.posts.value[0];
  page.showReplyInput(1, post.flattenedComments[0]);
  page.handleDelete('comment', post, post.flattenedComments[0]);
  await page.confirm();
  assert.equal(page.replyPost.value, null);
  assert.equal(page.replyComment.value, null);
});

test('个人主页删除后弹窗展示新评论关系，并保留展开和点赞状态', async () => {
  let deleted = false;
  const page = loadPage('page_social/social_profile/profile.vue', [
    'userPosts', 'selectedPost', 'fetchUserPosts', 'handleDeleteComment',
  ], {
    getPostList: async () => ({ code: 0, data: [postData(deleted)] }),
    deleteComment: async () => { deleted = true; return { code: 0 }; },
  });
  await page.fetchUserPosts();
  const post = page.userPosts.value[0];
  page.selectedPost.value = post;
  post.visibleCommentCount = 5;
  post.isLiked = true;
  post.likes = 1;
  page.handleDeleteComment(post, post.flattenedComments[0]);
  await page.confirm();
  assert.equal(page.selectedPost.value, page.userPosts.value[0]);
  assert.equal(page.selectedPost.value.comments, 1);
  assert.equal(page.selectedPost.value.flattenedComments[0].root_id, null);
  assert.equal(page.selectedPost.value.visibleCommentCount, 5);
  assert.equal(page.selectedPost.value.isLiked, true);
  assert.equal(page.selectedPost.value.likes, 1);
});
