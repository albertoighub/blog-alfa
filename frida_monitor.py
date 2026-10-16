import frida
import time
import sys

# --- Configuration ---
PROCESS_NAME = "Gears5.exe"
TARGET_FUNCTION_SIGNATURE = "CheckCosmeticUnlock" # Best guess based on user request

def on_message(message, data):
    """Callback function for receiving messages from the injected script."""
    if message['type'] == 'send':
        print(f"[+] Frida Message: {message['payload']}")

def hook_function():
    """Attaches to the process and sets up the hooks."""
    try:
        # Attach to the target process
        session = frida.attach(PROCESS_NAME)
        print(f"[*] Successfully attached to {PROCESS_NAME}")

        script = """
        // JavaScript code injected into the game process
        Java.perform(function() {
            console.log("[*] Frida script loaded successfully.");

            // Attempt to find and hook the target function
            var TargetModule = Module.findExportByName("Gears5.exe", "CheckCosmeticUnlock"); // Assuming it's an exported function
            if (TargetModule) {
                Interceptor.attach(TargetModule, {
                    onEnter: function(args) {
                        console.log("[*] CheckCosmeticUnlock called!");
                        // Log arguments if available (e.g., cosmetic ID, player state)
                        if (args[0]) {
                            console.log("    -> Arg 1 (Cosmetic ID): " + args[0].toInt32());
                        }
                    },
                    onLeave: function(retval) {
                        // Log the return value which determines if unlock is successful/available
                        var result = retval.toInt32();
                        console.log("    -> Return Value (Unlocked State): " + result);
                    }
                });
                console.log("[+] Successfully hooked CheckCosmeticUnlock.");
            } else {
                console.error("[-] Could not find the function: CheckCosmeticUnlock in Gears5.exe");
            }

        });
        """
        
        # Load and run the script
        script_obj = session.create_script(script)
        script_obj.on('message', on_message)
        script_obj.load()
        print("[*] Hooking script loaded. Game process must now be running.")

    except frida.ProcessNotFoundError:
        print(f"[!] Error: Process {PROCESS_NAME} not found. Please start the game first.")
    except Exception as e:
        print(f"[!] An unexpected error occurred: {e}")

if __name__ == '__main__':
    # Note: The user must manually ensure Gears5.exe is running before this script executes successfully.
    hook_function()
    # Keep the main thread alive to allow the injected script to run
    print("[*] Monitoring active. Press Ctrl+C to detach.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Detaching from process...")
        # In a real scenario, we would call session.detach() here if the session object was globally available/managed better.
        sys.exit(0)