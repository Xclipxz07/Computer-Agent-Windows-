import sys

print("--- DIAGNOSTIC START ---")

try:
    import screen_brightness_control as sbc
    print("screen_brightness_control imported.")
    try:
        current = sbc.get_brightness()
        print(f"Current brightness: {current}")
        # Try setting
        # sbc.set_brightness(50)
        # print("Set brightness to 50 works?")
    except Exception as e:
        print(f"SBC Error: {e}")
except ImportError as e:
    print(f"SBC Import Error: {e}")

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    print("pycaw imported.")
    
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current_vol = volume.GetMasterVolumeLevelScalar()
        print(f"Current Volume: {current_vol * 100}%")
    except Exception as e:
        print(f"Pycaw Error: {e}")
        
except ImportError as e:
    print(f"Pycaw Import Error: {e}")

print("--- DIAGNOSTIC END ---")
