# uts-tencentgeolocation腾讯定位插件使用文档

## API使用

参考[uni.getLocation](https://doc.dcloud.net.cn/uni-app-x/api/get-location.html)

## Android 平台

1. 申请腾讯地图key

[申请网址](https://lbs.qq.com/mobile/androidMapSDK/developerGuide/getKey)

2. 配置key到项目

在项目根目录下添加 AndroidManifest.xml 文件，详情参考：[Android原生应用清单文件](https://uniapp.dcloud.net.cn/tutorial/app-nativeresource-android.html#%E5%BA%94%E7%94%A8%E6%B8%85%E5%8D%95%E6%96%87%E4%BB%B6-androidmanifest-xml)。将申请的 key 配置到项目 AndroidManifest.xml 的 application 节点中，如下：
```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" xmlns:tools="http://schemas.android.com/tools"
>
  <application>

    <!-- 将申请到的 key 配置在 android:value 属性中 -->
    <meta-data android:name="TencentMapSDK" android:value="您申请的Key" />

  </application>

</manifest>
```

3. 制作自定义基座运行后生效
提交云端打包制作自定义基座后，再在HBuilderX中真机运行。

## iOS 平台（暂未支持）

1. 申请腾讯地图key

[申请网址](https://lbs.qq.com/mobile/androidMapSDK/developerGuide/getKey)

2. 配置key到插件中

在项目根目录下添加 Info.plist 文件，详情参考：[iOS原生应用配置文件](https://uniapp.dcloud.net.cn/tutorial/app-nativeresource-ios.html#infoplist)。将申请的 key 配置到项目 Info.plist 的 TencentLBSAPIKey 键值中，如下：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>TencentLBSAPIKey</key>
    <string>您申请的Key</string>
  </dict>
</plist>
```

3. 配置访问位置权限描述信息
在项目根目录下 Info.plist 文件中添加以下权限描述信息：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>NSLocationAlwaysUsageDescription</key>
    <string>后台运行期访问位置信息的许可描述</string>
    <key>NSLocationWhenInUseUsageDescription</key>
    <string>运行期访问位置信息的许可描述</string>
    <key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
    <string>访问位置信息的许可描述</string>
  </dict>
</plist>
```

> 许可描述信息需根据应用实际业务情况准确描述，否则可能无法通过 AppStore 上架审核
> uni-app 项目也可以在 manifest.json 的 "App权限配置" 可视化界面的 "iOS隐私信息访问的许可描述" 下配置

3. 制作自定义基座运行后生效
提交云端打包制作自定义基座后，再在HBuilderX中真机运行。

## 注意事项

### 隐私合规问题
此插件使用了腾讯位置服务SDK，调用定位API会采集个人隐私信息，在业务中请确保最终用户已经同意了App的隐私协议后再调用定位API，否则会因为隐私合规问题无法上架应用市场。

App的隐私政策中需披露使用的三方SDK相关情况：

- Android平台腾讯位置服务SDK [合规说明](https://lbs.qq.com/mobile/androidLocationSDK/androidLBSInfo)
- iOS平台腾讯位置服务SDK [合规说明](https://lbs.qq.com/mobile/iosLocationSDK/iosLBSInfo)


## 相关开发文档

- [UTS 语法](https://uniapp.dcloud.net.cn/tutorial/syntax-uts.html)
- [UTS 插件开发文档](https://doc.dcloud.net.cn/uni-app-x/plugin/uts-plugin.html)
