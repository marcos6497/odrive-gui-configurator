# hooks/hook-odrive.py

from PyInstaller.utils.hooks import collect_data_files

# Esta linha diz ao PyInstaller para encontrar o pacote 'odrive'
# e coletar TODOS os arquivos de dados dele, de forma recursiva.
# Isso inclui a pasta 'lib' e todas as DLLs dentro dela.
datas = collect_data_files('odrive', include_py_files=True)