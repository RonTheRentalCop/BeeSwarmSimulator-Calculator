import flet as ft

from bss_calc.app import ASSETS_DIR, main

if __name__ == "__main__":
    ft.run(main, assets_dir=str(ASSETS_DIR))
