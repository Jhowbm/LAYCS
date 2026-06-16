#!/usr/bin/env python3
"""
Script de inicialização automática para o Flashscore Lay Analyzer
Versão Python cross-platform
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    print("=" * 60)
    print("FLASHSCORE LAY ANALYZER - METODO DE CICLOS")
    print("Inicializacao Automatica - Um Clique para Comecar")
    print("=" * 60)

def check_venv():
    """Verifica e cria ambiente virtual se necessário"""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("[1/5] Criando ambiente virtual...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("    [OK] Ambiente virtual criado!")
        except subprocess.CalledProcessError as e:
            print(f"    [ERRO] Erro ao criar ambiente virtual: {e}")
            return False
    else:
        print("[1/5] Ambiente virtual encontrado!")
        print("    [OK] Ambiente virtual ja existe!")
    
    return True

def activate_venv():
    """Retorna o caminho do Python do ambiente virtual"""
    if os.name == 'nt':  # Windows
        python_path = Path("venv/Scripts/python.exe")
    else:  # Linux/Mac
        python_path = Path("venv/bin/python")
    
    if python_path.exists():
        print("[2/5] Usando Python do ambiente virtual!")
        print(f"    [OK] {python_path}")
        return str(python_path)
    else:
        print("[2/5] Ambiente virtual nao encontrado corretamente!")
        print("    [AVISO] Usando Python do sistema...")
        return sys.executable

def install_dependencies(python_path):
    """Instala as dependências necessárias"""
    print("[3/5] Instalando/verificando dependencias...")
    
    dependencies = [
        "flask",
        "selenium", 
        "beautifulsoup4",
        "pandas",
        "webdriver-manager",
        "openpyxl"
    ]
    
    try:
        subprocess.run([
            python_path, "-m", "pip", "install", "-q"
        ] + dependencies, check=True)
        print("    [OK] Dependencias instaladas/atualizadas!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"    [ERRO] Erro ao instalar dependencias: {e}")
        return False

def check_files():
    """Verifica se os arquivos necessários existem"""
    print("[4/5] Verificando arquivos do sistema...")
    
    required_files = [
        "app.py",
        "ciclos_manager.py",
        "analyzer.py",
        "scraper.py",
        "config.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"    [ERRO] Arquivos faltando: {', '.join(missing_files)}")
        return False
    
    print("    [OK] Todos os arquivos encontrados!")
    return True

def start_application(python_path):
    """Inicia a aplicação Flask"""
    print("[5/5] Iniciando aplicacao web...")
    print()
    print("=" * 60)
    print("APLICACAO INICIADA!")
    print("Acesse no navegador: http://localhost:5000")
    print("Pressione CTRL+C para parar o servidor")
    print("=" * 60)
    print()
    
    try:
        subprocess.run([python_path, "app.py"])
    except KeyboardInterrupt:
        print("\n\n    [STOP] Servidor parado pelo usuario.")
    except Exception as e:
        print(f"\n\n    [ERRO] Erro ao iniciar aplicacao: {e}")

def main():
    """Função principal"""
    print_banner()
    
    # Mudar para o diretório do script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Executar passos
    if not check_venv():
        print("\n[ERRO] Falha na configuracao do ambiente virtual.")
        input("Pressione ENTER para sair...")
        return
    
    python_path = activate_venv()
    
    if not install_dependencies(python_path):
        print("\n[ERRO] Falha na instalacao de dependencias.")
        input("Pressione ENTER para sair...")
        return
    
    if not check_files():
        print("\n[ERRO] Arquivos necessarios faltando.")
        input("Pressione ENTER para sair...")
        return
    
    start_application(python_path)

if __name__ == "__main__":
    main()