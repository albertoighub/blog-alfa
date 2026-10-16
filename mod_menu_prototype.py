# mod_menu_prototype.py

import time
from typing import Dict, Any

class GameProcess:
    """
    Simula el proceso de Gears of War 5. Contiene la lógica crítica del juego.
    En un entorno real (DLL Inyectada), esta clase interactuaría con la memoria
    del proceso principal a través de APIs como ReadProcessMemory/WriteProcessMemory.
    """
    def __init__(self):
        print("--- [Game Process] Inicializando el motor del juego...")
        # Simulación de los datos reales que el juego lee (Fuente de Verdad original)
        self._original_cosmetic_state: Dict[str, bool] = {
            "skin_a": False,  # Bloqueado originalmente
            "weapon_b": True, # Desbloqueado originalmente
            "emote_c": False
        }
        print("[Game Process] Datos de estado cosmético cargados (Estado Original).")

    def check_cosmetic_unlock(self, item_id: str) -> bool:
        """
        Función crítica del juego que verifica si un cosmético está desbloqueado.
        Esta es la función objetivo para el 'hooking'.
        Retorna True si está desbloqueado, False en caso contrario.
        """
        return self._original_cosmetic_state.get(item_id, False)

    def simulate_gameplay(self):
        """Simula un ciclo de juego donde se verifica el estado."""
        print("\n--- [Game Process] Simulando sesión de juego...")
        time.sleep(0.5) # Simulación de carga
        
        # Prueba 1: Ítem bloqueado (debería ser False)
        item_a = "skin_a"
        is_unlocked = self.check_cosmetic_unlock(item_a)
        print(f"[Game Process] Estado de '{item_a}': {'DESBLOQUEADO' if is_unlocked else 'BLOQUEADO'} (Original)")

        # Prueba 2: Ítem desbloqueado (debería ser True)
        item_b = "weapon_b"
        is_unlocked = self.check_cosmetic_unlock(item_b)
        print(f"[Game Process] Estado de '{item_b}': {'DESBLOQUEADO' if is_unlocked else 'BLOQUEADO'} (Original)")


class ModMenu:
    """
    Simula el Mod Menu, la interfaz que contiene la lógica de inyección/hooking.
    Esta clase representa la DLL que se carga en el proceso del juego.
    """
    def __init__(self, game_process: GameProcess):
        self.game = game_process
        self._is_mod_active = False
        print("\n--- [Mod Menu] Mod Menu cargado y listo para ser inyectado.")

    def activate_hook(self):
        """
        Simula la activación del 'Hook'. En un entorno real, esto reescribiría 
        la instrucción de memoria en el juego (NOP/JMP) para redirigir la llamada.
        Aquí simulamos la sobreescritura lógica.
        """
        if not self._is_mod_active:
            print("\n[Mod Menu] >>> INICIANDO HOOK DE PERSISTENCIA <<<")
            self._is_mod_active = True
            # En un entorno real, aquí se aplicaría el parche de memoria.
            print("[Mod Menu] Hook aplicado exitosamente. La lógica del juego ha sido sobrescrita.")

    def deactivate_hook(self):
        """Simula la desactivación del hook (retornando al estado original)."""
        if self._is_mod_active:
            print("\n[Mod Menu] >>> DESACTIVANDO HOOK DE PERSISTENCIA <<<")
            self._is_mod_active = False
            # En un entorno real, aquí se restaurarían las instrucciones originales de memoria.
            print("[Mod Menu] Hook desaplicado. El juego ha vuelto a su estado original.")

    def check_cosmetic_unlock(self, item_id: str) -> bool:
        """
        Función 'hookeada'. Sobrescribe la función original del proceso de juego.
        Si el mod está activo, siempre retorna True para cosméticos relevantes.
        """
        if self._is_mod_active and item_id in ["skin_a", "emote_c"]:
            # Esta es la modificación permanente que buscamos: forzar la verdad a TRUE.
            return True 
        
        # Si el mod no está activo o si el ítem no está en nuestra lista de 'hackeables',
        # llamamos al estado original del juego (GameProcess).
        return self.game.check_cosmetic_unlock(item_id)


def main():
    """Función principal que simula la ejecución del Mod Menu."""
    
    # 1. Inicialización: El proceso del juego se carga en memoria.
    game = GameProcess()

    # 2. Inyección: Cargamos el ModMenu (la DLL).
    mod_menu = ModMenu(game)

    print("\n=========================================================")
    print("           DEMO DE ARQUITECTURA DEL MOD MENU             ")
    print("=========================================================")

    # --- ESCENARIO 1: Juego sin el mod activo (Comportamiento Original) ---
    print("\n--- [ESCENARIO 1] JUGANDO SIN EL MOD ACTIVADO ---")
    game.simulate_gameplay() # skin_a debería ser BLOQUEADO

    time.sleep(2)

    # --- ESCENARIO 2: Activación del Mod Menu (Inyección/Hooking) ---
    mod_menu.activate_hook()

    # Reemplazamos la función crítica en el proceso de juego con nuestra versión 'hookeada'
    game.check_cosmetic_unlock = mod_menu.check_cosmetic_unlock 

    print("\n--- [ESCENARIO 2] JUGANDO CON EL MOD ACTIVADO (PERSISTENCIA) ---")
    # Ahora, al llamar a game.simulate_gameplay(), se llama a la función hookeada.
    game.simulate_gameplay() # skin_a debería ser DESBLOQUEADO

    time.sleep(2)

    # --- ESCENARIO 3: Desactivación del Mod Menu (Retorno al estado original) ---
    mod_menu.deactivate_hook()
    
    # Restauramos la función original para el cierre de sesión limpio
    game.check_cosmetic_unlock = game.check_cosmetic_unlock.__self__.check_cosmetic_unlock 

    print("\n--- [ESCENARIO 3] JUGANDO DESPUÉS DE DESACTIVAR EL MOD ---")
    game.simulate_gameplay() # skin_a debería volver a estar BLOQUEADO

if __name__ == "__main__":
    main()