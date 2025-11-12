# 🚀 PLAN: MIGRATION TỪ PYTHON SANG C#

> **Dự án:** Instagram Automation Tool
> **Mục tiêu:** Viết lại hoàn toàn từ Python sang C#
> **Ngày tạo:** 2025-11-12
> **Tác giả:** Migration Plan

---

## 📋 MỤC LỤC

1. [Tổng Quan Migration](#1-tổng-quan-migration)
2. [Technology Stack Mapping](#2-technology-stack-mapping)
3. [Architecture Design](#3-architecture-design)
4. [Module Migration Plan](#4-module-migration-plan)
5. [Code Examples](#5-code-examples)
6. [Step-by-Step Roadmap](#6-step-by-step-roadmap)
7. [Challenges & Solutions](#7-challenges--solutions)
8. [Testing Strategy](#8-testing-strategy)
9. [Timeline Estimate](#9-timeline-estimate)
10. [Resources](#10-resources)

---

## 1. TỔNG QUAN MIGRATION

### 1.1. Mục Đích

**Tại sao migrate sang C#?**
- ✅ **Performance:** C# nhanh hơn Python, đặc biệt với multi-threading
- ✅ **Type Safety:** Static typing giúp catch lỗi sớm hơn
- ✅ **Windows Native:** Tích hợp tốt hơn với Windows API
- ✅ **UI Framework:** WPF/WinUI 3 mạnh mẽ hơn Tkinter
- ✅ **Maintainability:** Code structure rõ ràng hơn với OOP mạnh
- ✅ **Deployment:** Single EXE dễ distribute hơn

### 1.2. Phạm Vi Project

**Chức năng cần migrate:**
- ✅ Quản lý VM (LDPlayer) và tài khoản Instagram
- ✅ Login tự động với 2FA
- ✅ Đăng bài tự động (video/ảnh)
- ✅ Download video từ YouTube/TikTok
- ✅ Scheduling và queue management
- ✅ Thread-safe VM resource locking
- ✅ Auto-updater
- ✅ Diagnostics và logging

**Không thay đổi:**
- ❌ Workflow logic (giữ nguyên)
- ❌ Data format (JSON configs)
- ❌ External dependencies (LDPlayer, ADB, Instagram)

---

## 2. TECHNOLOGY STACK MAPPING

### 2.1. Python → C# Mapping Table

| Component | Python (Current) | C# (Target) | Notes |
|-----------|------------------|-------------|-------|
| **Language** | Python 3.10+ | C# 12 (.NET 8) | LTS, modern features |
| **UI Framework** | CustomTkinter | WPF / WinUI 3 | Modern Windows UI |
| **Android Automation** | UIAutomator2 | AdvancedSharpAdbClient + custom wrapper | ADB-based |
| **HTTP Client** | requests | HttpClient | Built-in async |
| **Video Download** | yt-dlp (Python) | yt-dlp CLI wrapper | Process execution |
| **Video Processing** | ffmpeg (subprocess) | FFMpegCore | .NET wrapper |
| **JSON** | json module | System.Text.Json | Built-in |
| **Logging** | logging module | Serilog / NLog | Structured logging |
| **Threading** | threading module | Task / async-await | Modern async |
| **Dependency Injection** | N/A | Microsoft.Extensions.DependencyInjection | Best practice |
| **Build Tool** | PyInstaller | .NET Publish / MSIX | Native packaging |

### 2.2. Key Libraries

**C# NuGet Packages cần dùng:**

```xml
<!-- Core -->
<PackageReference Include="Microsoft.Extensions.DependencyInjection" Version="8.0.0" />
<PackageReference Include="Microsoft.Extensions.Logging" Version="8.0.0" />
<PackageReference Include="Serilog" Version="3.1.1" />
<PackageReference Include="Serilog.Sinks.File" Version="5.0.0" />

<!-- Android/ADB -->
<PackageReference Include="AdvancedSharpAdbClient" Version="2.5.6" />

<!-- HTTP & API -->
<PackageReference Include="System.Net.Http.Json" Version="8.0.0" />

<!-- Video Processing -->
<PackageReference Include="FFMpegCore" Version="5.1.0" />

<!-- JSON -->
<PackageReference Include="System.Text.Json" Version="8.0.0" />

<!-- UI (WPF) -->
<PackageReference Include="ModernWpfUI" Version="0.9.6" />
<PackageReference Include="CommunityToolkit.Mvvm" Version="8.2.2" />

<!-- OR UI (WinUI 3) - Alternative -->
<PackageReference Include="Microsoft.WindowsAppSDK" Version="1.5.0" />
<PackageReference Include="CommunityToolkit.WinUI.UI.Controls" Version="7.1.2" />
```

---

## 3. ARCHITECTURE DESIGN

### 3.1. Solution Structure

```
InstagramAutomationTool.sln
│
├── src/
│   ├── InstagramTool.Core/              # Core business logic
│   │   ├── Models/                      # Data models
│   │   ├── Services/                    # Business services
│   │   ├── Interfaces/                  # Abstractions
│   │   └── Constants/                   # Constants & configs
│   │
│   ├── InstagramTool.Infrastructure/    # External integrations
│   │   ├── ADB/                         # ADB & Android automation
│   │   ├── LDPlayer/                    # LDPlayer management
│   │   ├── Video/                       # Video download & processing
│   │   ├── Instagram/                   # Instagram automation
│   │   └── Storage/                     # File & config management
│   │
│   ├── InstagramTool.UI.WPF/            # WPF UI (Option 1)
│   │   ├── Views/                       # XAML views
│   │   ├── ViewModels/                  # MVVM ViewModels
│   │   ├── Converters/                  # Value converters
│   │   └── Resources/                   # Styles, themes
│   │
│   ├── InstagramTool.UI.WinUI/          # WinUI 3 (Option 2)
│   │   └── (same structure as WPF)
│   │
│   └── InstagramTool.Updater/           # Auto-updater app
│       └── Program.cs
│
├── tests/
│   ├── InstagramTool.Core.Tests/
│   ├── InstagramTool.Infrastructure.Tests/
│   └── InstagramTool.UI.Tests/
│
└── tools/
    └── build.ps1                        # Build & packaging script
```

### 3.2. Architecture Layers

```
┌─────────────────────────────────────────┐
│         UI Layer (WPF/WinUI)            │  ← ViewModels, Views
├─────────────────────────────────────────┤
│         Core Layer (Business Logic)     │  ← Services, Models
├─────────────────────────────────────────┤
│    Infrastructure (External Systems)    │  ← ADB, LDPlayer, APIs
├─────────────────────────────────────────┤
│       Cross-Cutting Concerns            │  ← Logging, DI, Config
└─────────────────────────────────────────┘
```

**Design Patterns:**
- ✅ **MVVM** - UI separation
- ✅ **Repository Pattern** - Data access
- ✅ **Dependency Injection** - Loose coupling
- ✅ **Singleton** - VM Manager, Config
- ✅ **Observer** - Event-driven logging
- ✅ **Factory** - Create services
- ✅ **Strategy** - Multiple downloaders

---

## 4. MODULE MIGRATION PLAN

### 4.1. Phase 1: Core Infrastructure (Week 1-2)

#### 📦 Module: `config.py` → `ConfigurationService.cs`

**Python:**
```python
def find_ldplayer_path():
    # Check registry, env vars, common paths
    return path
```

**C#:**
```csharp
public class ConfigurationService : IConfigurationService
{
    public string FindLDPlayerPath()
    {
        // 1. Check environment variable
        var envPath = Environment.GetEnvironmentVariable("LDPLAYER_PATH");
        if (IsValidLDPlayerPath(envPath)) return envPath;

        // 2. Check registry
        var registryPath = GetFromRegistry();
        if (IsValidLDPlayerPath(registryPath)) return registryPath;

        // 3. Check common paths
        var commonPaths = new[]
        {
            @"C:\LDPlayer\LDPlayer9",
            @"C:\Program Files\LDPlayer9",
            // ...
        };

        foreach (var path in commonPaths)
        {
            if (IsValidLDPlayerPath(path)) return path;
        }

        return null;
    }

    private string GetFromRegistry()
    {
        using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\LDPlayer9");
        return key?.GetValue("InstallDir") as string;
    }

    private bool IsValidLDPlayerPath(string path)
    {
        if (string.IsNullOrEmpty(path)) return false;
        return File.Exists(Path.Combine(path, "ldconsole.exe"));
    }
}
```

---

#### 📦 Module: `constants.py` → `Constants.cs`

**Python:**
```python
WAIT_SHORT = 2
XPATH_INSTAGRAM_APP = '//*[@text="Instagram"]'
```

**C#:**
```csharp
public static class InstagramConstants
{
    // Timing
    public static class Timing
    {
        public const int WaitShort = 2;
        public const int WaitMedium = 5;
        public const int WaitLong = 10;
        public const int TimeoutDefault = 15;
    }

    // XPath Selectors
    public static class XPath
    {
        public const string InstagramApp = @"//*[@text='Instagram']";
        public const string UsernameInput = @"//*[@text='Username, email or mobile number']";
        public const string PasswordInput = @"//*[@text='Password']";
        public const string LoginButton = @"//*[@text='Log in']";
        // ... more
    }

    // Resource IDs
    public static class ResourceId
    {
        public const string FeedTab = "com.instagram.android:id/feed_tab";
        public const string ProfileTab = "com.instagram.android:id/profile_tab";
        // ... more
    }
}
```

---

#### 📦 Module: `vm_manager.py` → `VmResourceManager.cs`

**Python:**
```python
class VMManager:
    _instance = None

    def acquire_vm(self, vm_name, timeout=300):
        vm_lock = self._vm_locks[vm_name]
        return vm_lock.acquire(blocking=True, timeout=timeout)
```

**C#:**
```csharp
public sealed class VmResourceManager : IVmResourceManager
{
    private static readonly Lazy<VmResourceManager> _instance =
        new(() => new VmResourceManager());

    private readonly ConcurrentDictionary<string, SemaphoreSlim> _vmLocks = new();
    private readonly ILogger<VmResourceManager> _logger;

    public static VmResourceManager Instance => _instance.Value;

    private VmResourceManager(ILogger<VmResourceManager> logger = null)
    {
        _logger = logger;
    }

    public async Task<bool> AcquireVmAsync(string vmName, int timeoutSeconds = 300)
    {
        var semaphore = _vmLocks.GetOrAdd(vmName, _ => new SemaphoreSlim(1, 1));

        _logger?.LogInformation("Attempting to acquire VM '{VmName}' (timeout={Timeout}s)",
            vmName, timeoutSeconds);

        var acquired = await semaphore.WaitAsync(TimeSpan.FromSeconds(timeoutSeconds));

        if (acquired)
        {
            _logger?.LogInformation("✅ Successfully acquired VM '{VmName}'", vmName);
        }
        else
        {
            _logger?.LogWarning("⏱️ Timeout waiting for VM '{VmName}' after {Timeout}s",
                vmName, timeoutSeconds);
        }

        return acquired;
    }

    public void ReleaseVm(string vmName)
    {
        if (_vmLocks.TryGetValue(vmName, out var semaphore))
        {
            semaphore.Release();
            _logger?.LogInformation("🔓 Released VM '{VmName}'", vmName);
        }
    }

    public bool IsVmLocked(string vmName)
    {
        if (!_vmLocks.TryGetValue(vmName, out var semaphore))
            return false;

        return semaphore.CurrentCount == 0;
    }
}
```

---

### 4.2. Phase 2: ADB & Android Automation (Week 2-3)

#### 📦 Module: `base_instagram.py` → `BaseInstagramAutomation.cs`

**C#:**
```csharp
public abstract class BaseInstagramAutomation
{
    protected readonly ILogger _logger;
    protected readonly Action<string, string> _logCallback;

    protected BaseInstagramAutomation(
        ILogger logger,
        Action<string, string> logCallback = null)
    {
        _logger = logger;
        _logCallback = logCallback;
    }

    protected void Log(string vmName, string message, LogLevel level = LogLevel.Information)
    {
        var formattedMsg = $"[{vmName}] {message}";
        _logger.Log(level, formattedMsg);
        _logCallback?.Invoke(vmName, message);
    }

    protected async Task<bool> SafeClickAsync(
        IAdbDevice device,
        string xpath,
        int timeout = 15,
        string vmName = "",
        int? sleepAfter = null,
        bool optional = false)
    {
        try
        {
            var element = await device.FindElementByXPathAsync(xpath, timeout);

            if (element != null)
            {
                await element.ClickAsync();
                Log(vmName, $"✅ Click thành công: {xpath.Substring(0, Math.Min(50, xpath.Length))}...");

                if (sleepAfter.HasValue)
                {
                    Log(vmName, $"⏱️ Chờ {sleepAfter}s sau khi click...");
                    await Task.Delay(TimeSpan.FromSeconds(sleepAfter.Value));
                }

                return true;
            }

            if (optional)
            {
                Log(vmName, $"⚠️ Không thấy (optional) → bỏ qua", LogLevel.Warning);
                return true;
            }

            Log(vmName, $"❌ Hết thời gian {timeout}s mà không tìm thấy", LogLevel.Error);
            return false;
        }
        catch (Exception ex)
        {
            Log(vmName, $"⚠️ Lỗi khi click: {ex.Message}", LogLevel.Error);
            return false;
        }
    }

    protected async Task<bool> SafeSendTextAsync(
        IAdbDevice device,
        string xpath,
        string text,
        int timeout = 15,
        int sleepAfter = 2,
        string vmName = "")
    {
        try
        {
            var element = await device.FindElementByXPathAsync(xpath, timeout);

            if (element != null)
            {
                await element.SendKeysAsync(text);
                Log(vmName, $"📝 Đã nhập text vào: {xpath.Substring(0, Math.Min(50, xpath.Length))}...");
                await Task.Delay(TimeSpan.FromSeconds(sleepAfter));
                return true;
            }

            Log(vmName, "❌ Không tìm thấy input field", LogLevel.Error);
            return false;
        }
        catch (Exception ex)
        {
            Log(vmName, $"⚠️ Lỗi nhập text: {ex.Message}", LogLevel.Error);
            return false;
        }
    }
}
```

---

#### 📦 Module: ADB Wrapper (NEW - C# specific)

**Create:** `AdbDeviceWrapper.cs`

```csharp
public interface IAdbDevice
{
    Task<IAdbElement> FindElementByXPathAsync(string xpath, int timeout);
    Task<bool> IsAppRunningAsync(string packageName);
    Task StartAppAsync(string packageName);
    Task StopAppAsync(string packageName);
    Task<string> GetDeviceSerialAsync();
}

public class AdbDeviceWrapper : IAdbDevice
{
    private readonly AdbClient _adbClient;
    private readonly DeviceData _device;
    private readonly ILogger<AdbDeviceWrapper> _logger;

    public AdbDeviceWrapper(string deviceSerial, ILogger<AdbDeviceWrapper> logger)
    {
        _logger = logger;
        _adbClient = new AdbClient();

        var devices = _adbClient.GetDevices();
        _device = devices.FirstOrDefault(d => d.Serial == deviceSerial)
            ?? throw new InvalidOperationException($"Device {deviceSerial} not found");
    }

    public async Task<IAdbElement> FindElementByXPathAsync(string xpath, int timeout)
    {
        var endTime = DateTime.Now.AddSeconds(timeout);

        while (DateTime.Now < endTime)
        {
            try
            {
                // Execute uiautomator dump and parse XML
                var uiDump = await ExecuteShellCommandAsync("uiautomator dump /dev/tty");
                var element = ParseXPathFromDump(uiDump, xpath);

                if (element != null)
                    return element;
            }
            catch (Exception ex)
            {
                _logger.LogWarning("Error finding element: {Error}", ex.Message);
            }

            await Task.Delay(500);
        }

        return null;
    }

    public async Task<bool> IsAppRunningAsync(string packageName)
    {
        var output = await ExecuteShellCommandAsync($"pidof {packageName}");
        return !string.IsNullOrWhiteSpace(output);
    }

    public async Task StartAppAsync(string packageName)
    {
        await ExecuteShellCommandAsync(
            $"monkey -p {packageName} -c android.intent.category.LAUNCHER 1");
    }

    public async Task StopAppAsync(string packageName)
    {
        await ExecuteShellCommandAsync($"am force-stop {packageName}");
    }

    private async Task<string> ExecuteShellCommandAsync(string command)
    {
        var receiver = new ConsoleOutputReceiver();
        await Task.Run(() => _adbClient.ExecuteRemoteCommand(command, _device, receiver));
        return receiver.ToString();
    }

    private IAdbElement ParseXPathFromDump(string xmlDump, string xpath)
    {
        // Parse XML and find element matching XPath
        // Implementation using XPath navigator
        // ...
        return null; // Placeholder
    }
}
```

---

### 4.3. Phase 3: Instagram Automation (Week 3-4)

#### 📦 Module: `login.py` → `InstagramLoginService.cs`

**C#:**
```csharp
public class InstagramLoginService : BaseInstagramAutomation, IInstagramLoginService
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IConfigurationService _configService;

    public InstagramLoginService(
        ILogger<InstagramLoginService> logger,
        IHttpClientFactory httpClientFactory,
        IConfigurationService configService,
        Action<string, string> logCallback = null)
        : base(logger, logCallback)
    {
        _httpClientFactory = httpClientFactory;
        _configService = configService;
    }

    public async Task<string> Get2FaCodeAsync(string key2Fa)
    {
        try
        {
            var cleanKey = Regex.Replace(key2Fa, @"\s+", "").ToUpper();
            var url = $"https://2fa.live/tok/{cleanKey}";

            using var client = _httpClientFactory.CreateClient();
            client.Timeout = TimeSpan.FromSeconds(8);

            var response = await client.GetAsync(url);
            response.EnsureSuccessStatusCode();

            var json = await response.Content.ReadFromJsonAsync<TwoFaResponse>();
            var code = json?.Token;

            if (string.IsNullOrEmpty(code) || code == "No token")
            {
                _logger.LogError("No token received from 2FA API");
                return null;
            }

            return code;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calling 2FA API");
            return null;
        }
    }

    public async Task<bool> AutoLoginAsync(
        string vmName,
        string adbAddress,
        string username,
        string password,
        string key2Fa)
    {
        IAdbDevice device = null;

        try
        {
            Log(vmName, $"🔌 Kết nối tới {adbAddress}");
            device = new AdbDeviceWrapper(adbAddress,
                LoggerFactory.Create(builder => {}).CreateLogger<AdbDeviceWrapper>());

            Log(vmName, "🔄 Bắt đầu đăng nhập...");

            // Close Chrome if showing
            if (await device.IsAppRunningAsync("com.android.chrome"))
            {
                await device.StopAppAsync("com.android.chrome");
                Log(vmName, "Đã đóng Chrome");
                await Task.Delay(TimeSpan.FromSeconds(InstagramConstants.Timing.WaitShort));
            }

            // Open Instagram
            Log(vmName, "📱 Mở ứng dụng Instagram...");
            if (!await SafeClickAsync(device, InstagramConstants.XPath.InstagramApp,
                sleepAfter: 30, vmName: vmName))
            {
                Log(vmName, "❌ Không tìm thấy app Instagram", LogLevel.Error);
                return false;
            }

            // Click "I already have an account" (optional)
            Log(vmName, "👤 Chọn 'I already have an account'...");
            await SafeClickAsync(device, InstagramConstants.XPath.AlreadyHaveAccount,
                sleepAfter: InstagramConstants.Timing.WaitMedium,
                vmName: vmName, optional: true);

            // Enter username
            Log(vmName, $"📝 Nhập username: {username}");
            if (!await SafeSendTextAsync(device, InstagramConstants.XPath.UsernameInput,
                username, sleepAfter: 4, vmName: vmName))
            {
                Log(vmName, "❌ Không thể nhập username", LogLevel.Error);
                return false;
            }

            // Enter password
            Log(vmName, "🔐 Nhập password");
            if (!await SafeSendTextAsync(device, InstagramConstants.XPath.PasswordInput,
                password, sleepAfter: InstagramConstants.Timing.WaitShort, vmName: vmName))
            {
                Log(vmName, "❌ Không thể nhập password", LogLevel.Error);
                return false;
            }

            // Click Login
            Log(vmName, "🔑 Nhấn Log in...");
            if (!await SafeClickAsync(device, InstagramConstants.XPath.LoginButton,
                sleepAfter: InstagramConstants.Timing.WaitLong, vmName: vmName))
            {
                Log(vmName, "❌ Không tìm thấy nút Log in", LogLevel.Error);
                return false;
            }

            // Handle 2FA
            Log(vmName, "🔄 Chọn Try another way...");
            await SafeClickAsync(device, InstagramConstants.XPath.TryAnotherWay,
                sleepAfter: InstagramConstants.Timing.WaitShort, vmName: vmName);

            Log(vmName, "📱 Chọn Authentication app...");
            await SafeClickAsync(device, InstagramConstants.XPath.AuthApp,
                sleepAfter: InstagramConstants.Timing.WaitShort, vmName: vmName);

            await SafeClickAsync(device, InstagramConstants.XPath.ContinueButton,
                sleepAfter: InstagramConstants.Timing.WaitMedium, vmName: vmName);

            // Get 2FA code
            Log(vmName, "🔒 Đang lấy mã 2FA...");
            var code = await Get2FaCodeAsync(key2Fa);

            if (string.IsNullOrEmpty(code))
            {
                Log(vmName, $"❌ Không lấy được mã 2FA", LogLevel.Error);
                return false;
            }

            Log(vmName, $"✅ Đã lấy mã 2FA: {code}");

            // Enter 2FA code
            Log(vmName, "📝 Nhập mã 2FA...");
            if (!await SafeSendTextAsync(device, InstagramConstants.XPath.CodeInput,
                code, sleepAfter: InstagramConstants.Timing.WaitShort, vmName: vmName))
            {
                Log(vmName, "❌ Không thể nhập mã 2FA", LogLevel.Error);
                return false;
            }

            // Continue
            Log(vmName, "▶️ Nhấn Continue...");
            if (!await SafeClickAsync(device, InstagramConstants.XPath.ContinueButton,
                sleepAfter: InstagramConstants.Timing.WaitLong, vmName: vmName))
            {
                Log(vmName, "⚠️ Không tìm thấy nút Continue", LogLevel.Warning);
                return false;
            }

            // Save login info
            Log(vmName, "💾 Lưu thông tin đăng nhập...");
            await SafeClickAsync(device, InstagramConstants.XPath.SaveButton,
                sleepAfter: InstagramConstants.Timing.WaitShort,
                vmName: vmName, optional: true);

            // Skip setup screens
            Log(vmName, "⏳ Bỏ qua màn hình setup...");
            await SafeClickAsync(device, InstagramConstants.XPath.SkipButton,
                vmName: vmName, optional: true);

            // Get Instagram name and save
            Log(vmName, "📝 Lấy tên tài khoản Instagram");
            await SafeClickAsync(device, InstagramConstants.XPath.ProfileTab,
                sleepAfter: InstagramConstants.Timing.WaitLong, vmName: vmName);

            // ... Get profile name and save to JSON ...

            Log(vmName, "✅ Chờ 5s trước khi kết thúc...");
            await Task.Delay(TimeSpan.FromSeconds(InstagramConstants.Timing.WaitMedium));

            await device.StopAppAsync("com.instagram.android");
            Log(vmName, "🛑 Đóng ứng dụng Instagram");

            return true;
        }
        catch (Exception ex)
        {
            Log(vmName, $"❌ Lỗi tự động đăng nhập: {ex.Message}", LogLevel.Error);
            _logger.LogException("Exception in AutoLoginAsync", ex);

            if (device != null)
            {
                try
                {
                    await device.StopAppAsync("com.instagram.android");
                }
                catch { }
            }

            return false;
        }
    }
}

// Helper class for 2FA API response
public record TwoFaResponse
{
    [JsonPropertyName("token")]
    public string Token { get; init; }
}
```

---

### 4.4. Phase 4: Video Download & Processing (Week 4)

#### 📦 Module: `download_dlp.py` → `VideoDownloadService.cs`

**C#:**
```csharp
public class VideoDownloadService : IVideoDownloadService
{
    private readonly ILogger<VideoDownloadService> _logger;
    private readonly IConfigurationService _configService;
    private readonly string _outputDir;

    public VideoDownloadService(
        ILogger<VideoDownloadService> logger,
        IConfigurationService configService)
    {
        _logger = logger;
        _configService = configService;
        _outputDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "temp");
        Directory.CreateDirectory(_outputDir);
    }

    public async Task<string> DownloadVideoAsync(
        string url,
        Action<string> logCallback = null)
    {
        try
        {
            var tempId = Guid.NewGuid().ToString("N")[..8];
            var outputTemplate = Path.Combine(_outputDir, $"{tempId}.%(ext)s");

            logCallback?.Invoke($"📥 Đang tải video từ: {url}");

            // Call yt-dlp as external process
            var ytdlpPath = await EnsureYtDlpInstalledAsync();

            var arguments = string.Join(" ",
                "-f", "\"bestvideo[vcodec^=avc1][height<=1080]+bestaudio[ext=m4a]/best[height<=1080]\"",
                "--merge-output-format", "mp4",
                "-o", $"\"{outputTemplate}\"",
                "--no-warnings",
                "--retries", "3",
                $"\"{url}\""
            );

            var process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = ytdlpPath,
                    Arguments = arguments,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true
                }
            };

            var outputBuilder = new StringBuilder();
            process.OutputDataReceived += (s, e) =>
            {
                if (!string.IsNullOrEmpty(e.Data))
                {
                    outputBuilder.AppendLine(e.Data);
                    logCallback?.Invoke(e.Data);
                }
            };

            process.Start();
            process.BeginOutputReadLine();
            await process.WaitForExitAsync();

            if (process.ExitCode != 0)
            {
                throw new Exception($"yt-dlp failed with exit code {process.ExitCode}");
            }

            // Find downloaded file
            var videoPath = Directory.GetFiles(_outputDir, $"{tempId}.*")
                .FirstOrDefault(f => f.EndsWith(".mp4") || f.EndsWith(".webm"));

            if (videoPath == null || !File.Exists(videoPath))
            {
                throw new FileNotFoundException("Downloaded video not found");
            }

            logCallback?.Invoke($"✅ Đã tải xong video");
            logCallback?.Invoke($"📁 File: {videoPath}");

            // Check and convert codec if needed
            await ConvertToH264IfNeededAsync(videoPath, tempId, logCallback);

            return videoPath;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error downloading video");
            logCallback?.Invoke($"❌ Lỗi tải video: {ex.Message}");
            return null;
        }
    }

    private async Task ConvertToH264IfNeededAsync(
        string videoPath,
        string tempId,
        Action<string> logCallback)
    {
        try
        {
            var mediaInfo = await FFProbe.AnalyseAsync(videoPath);
            var videoCodec = mediaInfo.PrimaryVideoStream?.CodecName?.ToLower();

            logCallback?.Invoke($"🎞️ Codec hiện tại: {videoCodec ?? "unknown"}");

            if (videoCodec != "h264" && videoCodec != "avc1")
            {
                var convertedPath = Path.Combine(_outputDir, $"converted_{tempId}.mp4");
                logCallback?.Invoke($"⚙️ Đang chuyển mã {videoCodec ?? "unknown"} → H.264 ...");

                await FFMpegArguments
                    .FromFileInput(videoPath)
                    .OutputToFile(convertedPath, true, options => options
                        .WithVideoCodec("libx264")
                        .WithConstantRateFactor(23)
                        .WithAudioCodec("aac")
                        .WithAudioBitrate(192)
                        .WithFastStart())
                    .ProcessAsynchronously();

                File.Delete(videoPath);
                File.Move(convertedPath, videoPath);

                logCallback?.Invoke("✅ Đã chuyển mã sang H.264 thành công.");
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Error checking/converting codec");
            logCallback?.Invoke("⚠️ Lỗi kiểm tra codec - Bỏ qua và tiếp tục");
        }
    }

    private async Task<string> EnsureYtDlpInstalledAsync()
    {
        var ytdlpPath = Path.Combine(_configService.ToolsDirectory, "yt-dlp.exe");

        if (!File.Exists(ytdlpPath))
        {
            _logger.LogInformation("Downloading yt-dlp...");

            using var client = new HttpClient();
            var ytdlpUrl = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe";
            var bytes = await client.GetByteArrayAsync(ytdlpUrl);
            await File.WriteAllBytesAsync(ytdlpPath, bytes);

            _logger.LogInformation("yt-dlp downloaded successfully");
        }

        return ytdlpPath;
    }
}
```

---

### 4.5. Phase 5: UI Layer (Week 5-6)

#### 📦 WPF UI - MVVM Structure

**MainViewModel.cs:**
```csharp
public class MainViewModel : ObservableObject
{
    private readonly IVmManagementService _vmService;
    private readonly IInstagramLoginService _loginService;
    private readonly ILogger<MainViewModel> _logger;

    public ObservableCollection<VmAccountViewModel> Accounts { get; }
    public ObservableCollection<string> LogMessages { get; }

    private VmAccountViewModel _selectedAccount;
    public VmAccountViewModel SelectedAccount
    {
        get => _selectedAccount;
        set => SetProperty(ref _selectedAccount, value);
    }

    public IAsyncRelayCommand AddAccountCommand { get; }
    public IAsyncRelayCommand LoginAccountCommand { get; }
    public IAsyncRelayCommand DeleteAccountCommand { get; }

    public MainViewModel(
        IVmManagementService vmService,
        IInstagramLoginService loginService,
        ILogger<MainViewModel> logger)
    {
        _vmService = vmService;
        _loginService = loginService;
        _logger = logger;

        Accounts = new ObservableCollection<VmAccountViewModel>();
        LogMessages = new ObservableCollection<string>();

        AddAccountCommand = new AsyncRelayCommand(AddAccountAsync);
        LoginAccountCommand = new AsyncRelayCommand(LoginAccountAsync, () => SelectedAccount != null);
        DeleteAccountCommand = new AsyncRelayCommand(DeleteAccountAsync, () => SelectedAccount != null);

        LoadAccountsAsync().FireAndForget();
    }

    private async Task LoadAccountsAsync()
    {
        try
        {
            var accounts = await _vmService.GetAllAccountsAsync();

            await Application.Current.Dispatcher.InvokeAsync(() =>
            {
                Accounts.Clear();
                foreach (var account in accounts)
                {
                    Accounts.Add(new VmAccountViewModel(account));
                }
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error loading accounts");
            AddLog($"❌ Lỗi tải danh sách: {ex.Message}");
        }
    }

    private async Task LoginAccountAsync()
    {
        if (SelectedAccount == null) return;

        try
        {
            SelectedAccount.IsLoggingIn = true;
            AddLog($"🔄 Bắt đầu đăng nhập {SelectedAccount.VmName}...");

            var success = await _loginService.AutoLoginAsync(
                SelectedAccount.VmName,
                SelectedAccount.AdbAddress,
                SelectedAccount.Username,
                SelectedAccount.Password,
                SelectedAccount.TwoFaKey,
                LogCallback);

            if (success)
            {
                AddLog($"✅ Đăng nhập thành công {SelectedAccount.VmName}");
            }
            else
            {
                AddLog($"❌ Đăng nhập thất bại {SelectedAccount.VmName}");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Login error");
            AddLog($"❌ Lỗi: {ex.Message}");
        }
        finally
        {
            SelectedAccount.IsLoggingIn = false;
        }
    }

    private void LogCallback(string vmName, string message)
    {
        Application.Current.Dispatcher.Invoke(() =>
        {
            AddLog($"[{vmName}] {message}");
        });
    }

    private void AddLog(string message)
    {
        var timestamp = DateTime.Now.ToString("HH:mm:ss");
        LogMessages.Add($"[{timestamp}] {message}");

        // Keep only last 1000 messages
        while (LogMessages.Count > 1000)
        {
            LogMessages.RemoveAt(0);
        }
    }
}
```

**MainWindow.xaml:**
```xml
<Window x:Class="InstagramTool.UI.WPF.Views.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:ui="http://schemas.modernwpf.com/2019"
        ui:WindowHelper.UseModernWindowStyle="True"
        Title="Instagram Automation Tool"
        Height="900" Width="1600">

    <Grid>
        <TabControl>
            <!-- Tab 1: Quản lý VM & Tài khoản -->
            <TabItem Header="👤 Quản lý VM &amp; Tài khoản">
                <Grid Margin="20">
                    <Grid.RowDefinitions>
                        <RowDefinition Height="Auto"/>
                        <RowDefinition Height="*"/>
                        <RowDefinition Height="200"/>
                    </Grid.RowDefinitions>

                    <!-- Toolbar -->
                    <StackPanel Orientation="Horizontal" Grid.Row="0" Margin="0,0,0,10">
                        <Button Content="➕ Thêm tài khoản"
                                Command="{Binding AddAccountCommand}"
                                Margin="0,0,10,0"/>
                        <Button Content="🔑 Đăng nhập"
                                Command="{Binding LoginAccountCommand}"
                                Margin="0,0,10,0"/>
                        <Button Content="🗑️ Xóa"
                                Command="{Binding DeleteAccountCommand}"
                                Margin="0,0,10,0"/>
                    </StackPanel>

                    <!-- Accounts DataGrid -->
                    <DataGrid Grid.Row="1"
                              ItemsSource="{Binding Accounts}"
                              SelectedItem="{Binding SelectedAccount}"
                              AutoGenerateColumns="False"
                              CanUserAddRows="False">
                        <DataGrid.Columns>
                            <DataGridTextColumn Header="VM Name" Binding="{Binding VmName}" Width="150"/>
                            <DataGridTextColumn Header="Instagram" Binding="{Binding InstaName}" Width="150"/>
                            <DataGridTextColumn Header="Username" Binding="{Binding Username}" Width="150"/>
                            <DataGridTextColumn Header="Password" Binding="{Binding Password}" Width="100"/>
                            <DataGridTextColumn Header="2FA Key" Binding="{Binding TwoFaKey}" Width="150"/>
                            <DataGridTextColumn Header="Port" Binding="{Binding Port}" Width="80"/>
                            <DataGridTextColumn Header="Status" Binding="{Binding Status}" Width="100"/>
                        </DataGrid.Columns>
                    </DataGrid>

                    <!-- Log Panel -->
                    <GroupBox Header="📝 Log" Grid.Row="2" Margin="0,10,0,0">
                        <ListBox ItemsSource="{Binding LogMessages}"
                                 ScrollViewer.VerticalScrollBarVisibility="Auto"
                                 ScrollViewer.HorizontalScrollBarVisibility="Auto"/>
                    </GroupBox>
                </Grid>
            </TabItem>

            <!-- Tab 2: Đặt lịch đăng bài -->
            <TabItem Header="📅 Đặt lịch đăng bài">
                <!-- TODO: Post scheduling UI -->
            </TabItem>

            <!-- Tab 3: Theo dõi & Tự động -->
            <TabItem Header="▶️ Theo dõi &amp; Tự động">
                <!-- TODO: Follow automation UI -->
            </TabItem>
        </TabControl>
    </Grid>
</Window>
```

---

## 5. CODE EXAMPLES

### 5.1. Dependency Injection Setup

**Program.cs (WPF with DI):**
```csharp
public partial class App : Application
{
    private ServiceProvider _serviceProvider;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        var services = new ServiceCollection();
        ConfigureServices(services);
        _serviceProvider = services.BuildServiceProvider();

        var mainWindow = _serviceProvider.GetRequiredService<MainWindow>();
        mainWindow.Show();
    }

    private void ConfigureServices(IServiceCollection services)
    {
        // Logging
        services.AddLogging(builder =>
        {
            builder.AddSerilog(new LoggerConfiguration()
                .MinimumLevel.Information()
                .WriteTo.File("logs/app.log", rollingInterval: RollingInterval.Day)
                .WriteTo.Console()
                .CreateLogger());
        });

        // HTTP Client
        services.AddHttpClient();

        // Core Services (Singleton)
        services.AddSingleton<IConfigurationService, ConfigurationService>();
        services.AddSingleton<IVmResourceManager, VmResourceManager>();

        // Business Services (Scoped)
        services.AddScoped<IVmManagementService, VmManagementService>();
        services.AddScoped<IInstagramLoginService, InstagramLoginService>();
        services.AddScoped<IInstagramPostService, InstagramPostService>();
        services.AddScoped<IVideoDownloadService, VideoDownloadService>();

        // ViewModels
        services.AddTransient<MainViewModel>();
        services.AddTransient<PostViewModel>();
        services.AddTransient<FollowViewModel>();

        // Views
        services.AddTransient<MainWindow>();
    }

    protected override void OnExit(ExitEventArgs e)
    {
        _serviceProvider?.Dispose();
        base.OnExit(e);
    }
}
```

---

### 5.2. Async/Await Pattern

**Good Practice:**
```csharp
// ✅ GOOD - Proper async/await
public async Task<bool> ProcessVideoAsync(string url)
{
    try
    {
        // Download video (IO-bound)
        var videoPath = await _videoService.DownloadVideoAsync(url);
        if (videoPath == null) return false;

        // Convert if needed (CPU-bound on thread pool)
        await Task.Run(() => ConvertVideo(videoPath));

        // Upload to Instagram (IO-bound)
        var success = await _instagramService.PostVideoAsync(videoPath);

        return success;
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "Error processing video");
        return false;
    }
}

// ❌ BAD - Blocking calls
public bool ProcessVideo(string url)
{
    var videoPath = _videoService.DownloadVideoAsync(url).Result; // Deadlock risk!
    // ...
}
```

---

### 5.3. Thread-Safe Collections

```csharp
// ✅ GOOD - Thread-safe
private readonly ConcurrentDictionary<string, VmStatus> _vmStatuses = new();

public void UpdateVmStatus(string vmName, VmStatus status)
{
    _vmStatuses.AddOrUpdate(vmName, status, (key, old) => status);
}

// ❌ BAD - Not thread-safe
private readonly Dictionary<string, VmStatus> _vmStatuses = new();

public void UpdateVmStatus(string vmName, VmStatus status)
{
    _vmStatuses[vmName] = status; // Race condition!
}
```

---

## 6. STEP-BY-STEP ROADMAP

### 📅 Week 1-2: Foundation & Core

**Day 1-2: Project Setup**
- [ ] Create solution structure
- [ ] Setup NuGet packages
- [ ] Configure logging (Serilog)
- [ ] Setup DI container
- [ ] Create base models and interfaces

**Day 3-4: Configuration & Constants**
- [ ] Migrate `config.py` → `ConfigurationService.cs`
- [ ] Migrate `constants.py` → `Constants.cs`
- [ ] Auto-detect LDPlayer path
- [ ] Read/write JSON configs

**Day 5-7: VM Resource Manager**
- [ ] Migrate `vm_manager.py` → `VmResourceManager.cs`
- [ ] Implement Semaphore-based locking
- [ ] Add wait for VM ready/stopped
- [ ] Unit tests for thread safety

**Day 8-10: LDPlayer Integration**
- [ ] Wrap ldconsole.exe commands
- [ ] VM start/stop/list operations
- [ ] VM configuration management
- [ ] Error handling and logging

---

### 📅 Week 2-3: ADB & Android Automation

**Day 11-13: ADB Client Setup**
- [ ] Install AdvancedSharpAdbClient
- [ ] Create `AdbDeviceWrapper.cs`
- [ ] Implement device connection
- [ ] Shell command execution
- [ ] File transfer (push/pull)

**Day 14-16: UI Automation Wrapper**
- [ ] UIAutomator dump parsing
- [ ] XPath element finding
- [ ] Click/SendKeys operations
- [ ] Wait for element helpers
- [ ] Base automation class

**Day 17-18: Testing & Debugging**
- [ ] Test ADB operations on real device
- [ ] Test element finding
- [ ] Performance tuning
- [ ] Error handling

---

### 📅 Week 3-4: Instagram Automation

**Day 19-21: Login Service**
- [ ] Migrate `login.py` → `InstagramLoginService.cs`
- [ ] 2FA API integration
- [ ] Login flow automation
- [ ] Save Instagram name to JSON
- [ ] Error recovery

**Day 22-24: Post Service**
- [ ] Migrate `post.py` → `InstagramPostService.cs`
- [ ] Post creation flow
- [ ] Caption handling
- [ ] Upload monitoring
- [ ] Error recovery

**Day 25-26: File Transfer**
- [ ] Migrate `send_file.py` → `FileTransferService.cs`
- [ ] ADB push implementation
- [ ] MediaStore scan broadcast
- [ ] DCIM cleanup

**Day 27-28: Testing**
- [ ] End-to-end login test
- [ ] End-to-end post test
- [ ] Error scenario testing

---

### 📅 Week 4: Video Download & Processing

**Day 29-30: Video Download Service**
- [ ] Migrate `download_dlp.py` → `VideoDownloadService.cs`
- [ ] yt-dlp wrapper
- [ ] YouTube download
- [ ] TikTok download

**Day 31-32: Video Processing**
- [ ] FFMpegCore integration
- [ ] Codec detection
- [ ] H.264 conversion
- [ ] Video validation

---

### 📅 Week 5-6: UI Layer

**Day 33-35: WPF Setup**
- [ ] Choose UI framework (WPF vs WinUI 3)
- [ ] Setup ModernWPF/WinUI
- [ ] Create main window structure
- [ ] Tab navigation

**Day 36-38: Users Tab**
- [ ] VM list DataGrid
- [ ] Add/Edit/Delete accounts
- [ ] Login button and progress
- [ ] Log viewer

**Day 39-41: Post Tab**
- [ ] Video URL input
- [ ] Download progress
- [ ] Schedule picker
- [ ] Post queue management

**Day 42-44: Follow Tab**
- [ ] Follow automation UI
- [ ] Like/Comment features
- [ ] Batch operations

---

### 📅 Week 7: Polish & Deployment

**Day 45-46: Auto Updater**
- [ ] GitHub release checker
- [ ] Download & extract updates
- [ ] Restart application

**Day 47-48: Build & Packaging**
- [ ] .NET Publish configuration
- [ ] Single-file executable
- [ ] MSIX packaging (optional)
- [ ] Installer creation

**Day 49-50: Documentation**
- [ ] Update README.md
- [ ] User guide
- [ ] Developer documentation
- [ ] Migration notes

---

## 7. CHALLENGES & SOLUTIONS

### ⚠️ Challenge 1: UIAutomator2 Equivalent in C#

**Problem:** Python's `uiautomator2` library không có equivalent trực tiếp trong C#.

**Solution:**
- Sử dụng `AdvancedSharpAdbClient` để giao tiếp với ADB
- Gọi `uiautomator dump` qua shell command
- Parse XML output để tìm elements
- Simulate clicks qua tọa độ hoặc input tap

**Alternative:** Sử dụng Appium.WebDriver for .NET (nặng hơn nhưng đầy đủ features)

---

### ⚠️ Challenge 2: yt-dlp Integration

**Problem:** yt-dlp là Python tool, không có .NET native library.

**Solution:**
- Option 1: Gọi yt-dlp.exe như external process (recommended - đơn giản)
- Option 2: Sử dụng YoutubeExplode library (.NET native - giới hạn hơn)
- Option 3: Wrap Python yt-dlp bằng IronPython (phức tạp)

**Recommended:** Option 1 - Gọi yt-dlp.exe, dễ maintain và update

---

### ⚠️ Challenge 3: Threading Model

**Problem:** Python's GIL vs C#'s true multi-threading

**Solution:**
- Python: `threading.Lock` → C#: `SemaphoreSlim` (async-friendly)
- Python: `threading.Thread` → C#: `Task.Run` hoặc `async/await`
- Sử dụng `ConcurrentDictionary` thay vì `Dictionary` với locks

---

### ⚠️ Challenge 4: UI Framework Choice

**Problem:** WPF vs WinUI 3?

**Comparison:**

| Feature | WPF | WinUI 3 |
|---------|-----|---------|
| Maturity | ✅ Mature, stable | ⚠️ Newer, evolving |
| Performance | ✅ Good | ✅ Better |
| Modern UI | ⚠️ Need ModernWPF | ✅ Native modern |
| Learning Curve | ✅ Easier | ⚠️ Steeper |
| Windows 10/11 | ✅ Both | ⚠️ Win10 1809+ |
| Deployment | ✅ Simple .exe | ⚠️ MSIX preferred |

**Recommendation:**
- **WPF with ModernWPF** - Nếu cần deploy đơn giản (single EXE)
- **WinUI 3** - Nếu target Windows 11 và muốn UI hiện đại nhất

---

### ⚠️ Challenge 5: Error Handling

**Problem:** Instagram UI thay đổi thường xuyên

**Solution:**
- Implement retry logic với exponential backoff
- Fallback XPath selectors (multiple options)
- Screenshot on error để debug
- Graceful degradation (skip optional steps)

**Code Pattern:**
```csharp
public async Task<bool> SafeClickWithRetryAsync(
    IAdbDevice device,
    string[] xpathOptions,
    int maxRetries = 3)
{
    for (int i = 0; i < maxRetries; i++)
    {
        foreach (var xpath in xpathOptions)
        {
            if (await SafeClickAsync(device, xpath))
                return true;
        }

        await Task.Delay(TimeSpan.FromSeconds(2));
    }

    return false;
}
```

---

## 8. TESTING STRATEGY

### 8.1. Unit Tests

**Frameworks:** xUnit + Moq + FluentAssertions

**Test Coverage:**
```csharp
[Fact]
public async Task VmResourceManager_AcquireVm_ShouldLockSuccessfully()
{
    // Arrange
    var manager = VmResourceManager.Instance;
    var vmName = "test-vm";

    // Act
    var acquired = await manager.AcquireVmAsync(vmName, timeout: 5);

    // Assert
    acquired.Should().BeTrue();
    manager.IsVmLocked(vmName).Should().BeTrue();

    // Cleanup
    manager.ReleaseVm(vmName);
}

[Fact]
public async Task VmResourceManager_AcquireVm_ShouldTimeoutWhenLocked()
{
    // Arrange
    var manager = VmResourceManager.Instance;
    var vmName = "test-vm";
    await manager.AcquireVmAsync(vmName);

    // Act
    var acquired = await manager.AcquireVmAsync(vmName, timeout: 1);

    // Assert
    acquired.Should().BeFalse();

    // Cleanup
    manager.ReleaseVm(vmName);
}
```

---

### 8.2. Integration Tests

**Test với LDPlayer thật:**
```csharp
[Fact]
[Trait("Category", "Integration")]
public async Task AdbDevice_ConnectToEmulator_ShouldSucceed()
{
    // Arrange
    var device = new AdbDeviceWrapper("emulator-5555", _logger);

    // Act
    var serial = await device.GetDeviceSerialAsync();

    // Assert
    serial.Should().Be("emulator-5555");
}
```

---

### 8.3. UI Tests

**Sử dụng WPF UI Testing:**
- FlaUI (Windows UI Automation)
- Manual QA testing
- Screenshot comparison

---

## 9. TIMELINE ESTIMATE

### 📊 Effort Breakdown

| Phase | Duration | Complexity | Risk |
|-------|----------|------------|------|
| Phase 1: Core Infrastructure | 2 weeks | Medium | Low |
| Phase 2: ADB Automation | 1.5 weeks | High | Medium |
| Phase 3: Instagram Logic | 1.5 weeks | Medium | High |
| Phase 4: Video Download | 1 week | Low | Low |
| Phase 5: UI Layer | 2 weeks | Medium | Low |
| Phase 6: Testing & Polish | 1 week | Low | Low |
| **Total** | **~9 weeks** | - | - |

**Assumptions:**
- 1 developer full-time
- Familiar với C# và WPF
- LDPlayer và Instagram không có breaking changes

**Realistic Timeline:** 10-12 weeks (với buffer cho bugs và learning curve)

---

## 10. RESOURCES

### 10.1. Documentation

**C# & .NET:**
- [Microsoft .NET Docs](https://learn.microsoft.com/en-us/dotnet/)
- [C# Programming Guide](https://learn.microsoft.com/en-us/dotnet/csharp/)
- [Async/Await Best Practices](https://learn.microsoft.com/en-us/archive/msdn-magazine/2013/march/async-await-best-practices-in-asynchronous-programming)

**WPF:**
- [WPF Documentation](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/)
- [ModernWPF UI Library](https://github.com/Kinnara/ModernWpf)
- [MVVM Toolkit](https://learn.microsoft.com/en-us/dotnet/communitytoolkit/mvvm/)

**WinUI 3:**
- [WinUI 3 Docs](https://learn.microsoft.com/en-us/windows/apps/winui/winui3/)
- [Windows App SDK](https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/)

**ADB & Android:**
- [AdvancedSharpAdbClient](https://github.com/yungd1plomat/AdvancedSharpAdbClient)
- [Android Debug Bridge](https://developer.android.com/tools/adb)
- [UIAutomator](https://developer.android.com/training/testing/other-components/ui-automator)

**Video Processing:**
- [FFMpegCore](https://github.com/rosenbjerg/FFMpegCore)
- [YoutubeExplode](https://github.com/Tyrrrz/YoutubeExplode)

---

### 10.2. Tools

**Development:**
- Visual Studio 2022 (Community/Professional)
- JetBrains Rider (Alternative)
- Git for version control
- LINQPad (for C# scripting/testing)

**Testing:**
- xUnit / NUnit
- Moq (mocking framework)
- FluentAssertions
- FlaUI (UI testing)

**Build & Deploy:**
- .NET CLI (dotnet publish)
- Advanced Installer / Inno Setup
- MSIX Packaging Tool (for Store deployment)

---

### 10.3. Sample Projects

**Reference C# Projects:**
- [WPF Modern UI Sample](https://github.com/Kinnara/ModernWpf/tree/master/samples)
- [MVVM Sample Apps](https://github.com/CommunityToolkit/MVVM-Samples)
- [ADB Client Examples](https://github.com/yungd1plomat/AdvancedSharpAdbClient/tree/master/AdvancedSharpAdbClient.Examples)

---

## 📌 CHECKLIST TỔNG HỢP

### ✅ Pre-Development
- [ ] Đọc và hiểu toàn bộ Python codebase
- [ ] Setup development environment (VS2022, .NET 8 SDK)
- [ ] Install LDPlayer và ADB tools
- [ ] Quyết định UI framework (WPF vs WinUI 3)
- [ ] Tạo GitHub repository mới

### ✅ Phase 1: Core (Week 1-2)
- [ ] Create solution structure
- [ ] Migrate config.py
- [ ] Migrate constants.py
- [ ] Migrate vm_manager.py
- [ ] Unit tests cho core modules

### ✅ Phase 2: ADB (Week 2-3)
- [ ] Setup AdvancedSharpAdbClient
- [ ] Create AdbDeviceWrapper
- [ ] Implement element finding
- [ ] Test trên real device

### ✅ Phase 3: Instagram (Week 3-4)
- [ ] Migrate login.py
- [ ] Migrate post.py
- [ ] Migrate send_file.py
- [ ] End-to-end testing

### ✅ Phase 4: Video (Week 4)
- [ ] Migrate download_dlp.py
- [ ] FFMpegCore integration
- [ ] Test YouTube & TikTok downloads

### ✅ Phase 5: UI (Week 5-6)
- [ ] Setup WPF/WinUI project
- [ ] Create MainWindow và tabs
- [ ] Implement MVVM ViewModels
- [ ] Data binding và commands

### ✅ Phase 6: Polish (Week 7)
- [ ] Auto-updater
- [ ] Build script
- [ ] Documentation
- [ ] Final testing

### ✅ Deployment
- [ ] Create installer
- [ ] GitHub release
- [ ] User guide
- [ ] Migration completed ✨

---

## 🎯 NEXT STEPS

**Để bắt đầu ngay:**

1. **Clone repository hiện tại** để reference
2. **Tạo solution mới:** `dotnet new sln -n InstagramAutomationTool`
3. **Tạo projects theo structure** ở Section 3.1
4. **Cài NuGet packages** theo Section 2.2
5. **Bắt đầu với Phase 1:** Migrate config và constants
6. **Follow roadmap** từng tuần theo Section 6

**Questions? Issues?**
- Reference lại file `claude.md` gốc để hiểu logic
- Check code examples trong Plan.md này
- Test từng module nhỏ trước khi integration

---

**Good luck! 🚀**

*Nếu cần clarification hoặc code examples cho bất kỳ phần nào, hãy hỏi!*
