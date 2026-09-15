#!/usr/bin/env python3
"""
Script para gerar tabelas bonitas em PNG a partir dos resultados dos testes.

Uso:
    python scripts/generate_tables.py --quick results/quick_comparison.json
    python scripts/generate_tables.py --locust results/locust_comparison.json
    python scripts/generate_tables.py --all
"""

import json
import argparse
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.table import Table
    import numpy as np
except ImportError:
    print("ERRO: matplotlib não está instalado.")
    print("Instale com: pip install matplotlib")
    exit(1)


def create_output_dir():
    """Cria o diretório de saída se não existir"""
    output_dir = Path("results/tables")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def format_number(value: float, decimals: int = 2) -> str:
    """Formata número com casas decimais"""
    if value == 0:
        return "0.00"
    return f"{value:.{decimals}f}"


def format_percentage(value: float) -> str:
    """Formata porcentagem com sinal"""
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def get_color_for_difference(diff: float) -> str:
    """Retorna cor baseada na diferença percentual"""
    if abs(diff) < 5:
        return "#E8F5E9"  # Verde claro - diferença marginal
    elif diff < -10:
        return "#C8E6C9"  # Verde - Cache muito melhor
    elif diff > 10:
        return "#FFCDD2"  # Vermelho claro - DB muito melhor
    else:
        return "#FFF9C4"  # Amarelo claro - diferença moderada


def create_quick_latency_table(data: Dict[str, Any], output_dir: Path) -> str:
    """Cria tabela de resultados de latência individual"""
    
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('tight')
    ax.axis('off')
    
    # Dados da tabela
    endpoints = {
        "get_recommendation": "GET /recommendations/{user_id}",
        "post_feedback": "POST /recommendations/feedback",
        "get_stats": "GET /recommendations/stats/{user_id}"
    }
    
    # Cabeçalho
    headers = ["Endpoint", "Métrica", "DB (ms)", "Cache (ms)", "Diferença"]
    
    # Preparar dados
    table_data = []
    for endpoint_key, endpoint_name in endpoints.items():
        if endpoint_key in data.get("comparison", {}):
            comp = data["comparison"][endpoint_key]
            metrics = comp["metric"]
            db_values = comp["bd"]
            cache_values = comp["cache"]
            diffs = comp["difference_pct"]
            
            for i, metric in enumerate(metrics):
                metric_name = metric.upper()
                db_val = db_values[i]
                cache_val = cache_values[i]
                diff = diffs[i]
                
                table_data.append([
                    endpoint_name if i == 0 else "",
                    metric_name,
                    format_number(db_val),
                    format_number(cache_val),
                    format_percentage(diff)
                ])
    
    # Criar tabela
    table = ax.table(
        cellText=table_data,
        colLabels=headers,
        cellLoc='center',
        loc='center',
        bbox=[0, 0, 1, 1]
    )
    
    # Estilizar cabeçalho
    for i in range(len(headers)):
        cell = table[(0, i)]
        cell.set_facecolor("#1976D2")
        cell.set_text_props(weight='bold', color='white', fontsize=14)
        cell.set_height(0.08)
    
    # Estilizar células
    row_idx = 1
    for endpoint_key in endpoints.keys():
        if endpoint_key in data.get("comparison", {}):
            comp = data["comparison"][endpoint_key]
            diffs = comp["difference_pct"]
            
            for i, diff in enumerate(diffs):
                # Primeira coluna (endpoint) - fundo cinza claro
                if i == 0:
                    cell = table[(row_idx, 0)]
                    cell.set_facecolor("#F5F5F5")
                    cell.set_text_props(weight='bold', fontsize=38)
                
                # Coluna de diferença - cor baseada no valor
                diff_cell = table[(row_idx, 4)]
                color = get_color_for_difference(diff)
                diff_cell.set_facecolor(color)
                
                if abs(diff) > 10:
                    diff_cell.set_text_props(weight='bold', fontsize=38)
                
                row_idx += 1
    
    # Ajustar altura das linhas
    for i in range(1, len(table_data) + 1):
        for j in range(len(headers)):
            table[(i, j)].set_height(0.06)
    
    # Título
    title = "Comparação de Latência: DB vs Cache\n(Testes de Latência Individual - 100 iterações)"
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    
    # Legenda
    legend_elements = [
        mpatches.Patch(facecolor="#C8E6C9", label="Cache >10% melhor"),
        mpatches.Patch(facecolor="#E8F5E9", label="Diferença <5% (marginal)"),
        mpatches.Patch(facecolor="#FFF9C4", label="Diferença 5-10% (moderada)"),
        mpatches.Patch(facecolor="#FFCDD2", label="DB >10% melhor")
    ]
    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.05), ncol=4)
    
    plt.tight_layout()
    
    # Salvar
    output_path = output_dir / "tabela_latencia_quick.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return str(output_path)


def create_quick_detailed_table(data: Dict[str, Any], output_dir: Path) -> str:
    """Cria tabela detalhada de latência com todas as métricas"""
    
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.axis('tight')
    ax.axis('off')
    
    endpoints = {
        "get_recommendation": "GET /recommendations/{user_id}",
        "post_feedback": "POST /recommendations/feedback",
        "get_stats": "GET /recommendations/stats/{user_id}"
    }
    
    headers = ["Endpoint", "Métrica", "DB (ms)", "Cache (ms)", "Diferença %", "Taxa Sucesso"]
    
    table_data = []
    for endpoint_key, endpoint_name in endpoints.items():
        bd_data = data.get("bd_results", {}).get("endpoints", {}).get(endpoint_key, {})
        cache_data = data.get("cache_results", {}).get("endpoints", {}).get(endpoint_key, {})
        
        metrics = ["mean", "median", "p95", "p99", "min", "max"]
        metric_names = ["Média", "Mediana", "P95", "P99", "Mínima", "Máxima"]
        
        for metric, metric_name in zip(metrics, metric_names):
            db_val = bd_data.get(metric, 0)
            cache_val = cache_data.get(metric, 0)
            
            if db_val > 0:
                diff = ((cache_val - db_val) / db_val) * 100
            else:
                diff = 0
            
            success_rate = cache_data.get("success_rate", 100.0)
            
            table_data.append([
                endpoint_name if metric == "mean" else "",
                metric_name,
                format_number(db_val),
                format_number(cache_val),
                format_percentage(diff),
                f"{success_rate:.1f}%"
            ])
    
    table = ax.table(
        cellText=table_data,
        colLabels=headers,
        cellLoc='center',
        loc='center',
        bbox=[0, 0, 1, 1]
    )
    
    # Estilizar cabeçalho
    for i in range(len(headers)):
        cell = table[(0, i)]
        cell.set_facecolor("#1976D2")
        cell.set_text_props(weight='bold', color='white', fontsize=14)
        cell.set_height(0.06)
    
    # Estilizar células
    row_idx = 1
    for endpoint_key in endpoints.keys():
        bd_data = data.get("bd_results", {}).get("endpoints", {}).get(endpoint_key, {})
        cache_data = data.get("cache_results", {}).get("endpoints", {}).get(endpoint_key, {})
        
        metrics = ["mean", "median", "p95", "p99", "min", "max"]
        
        for i, metric in enumerate(metrics):
            if i == 0:
                cell = table[(row_idx, 0)]
                cell.set_facecolor("#F5F5F5")
                cell.set_text_props(weight='bold', fontsize=38)
            
            db_val = bd_data.get(metric, 0)
            cache_val = cache_data.get(metric, 0)
            
            if db_val > 0:
                diff = ((cache_val - db_val) / db_val) * 100
            else:
                diff = 0
            
            diff_cell = table[(row_idx, 4)]
            color = get_color_for_difference(diff)
            diff_cell.set_facecolor(color)
            
            if abs(diff) > 10:
                diff_cell.set_text_props(weight='bold', fontsize=38)
            
            row_idx += 1
    
    for i in range(1, len(table_data) + 1):
        for j in range(len(headers)):
            table[(i, j)].set_height(0.05)
    
    title = "Tabela Detalhada de Latência: DB vs Cache\n(Todas as Métricas - Testes de Latência Individual)"
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    
    legend_elements = [
        mpatches.Patch(facecolor="#C8E6C9", label="Cache >10% melhor"),
        mpatches.Patch(facecolor="#E8F5E9", label="Diferença <5% (marginal)"),
        mpatches.Patch(facecolor="#FFF9C4", label="Diferença 5-10% (moderada)"),
        mpatches.Patch(facecolor="#FFCDD2", label="DB >10% melhor")
    ]
    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.02), ncol=4)
    
    plt.tight_layout()
    
    output_path = output_dir / "tabela_latencia_detalhada.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return str(output_path)


def create_locust_table(data: Dict[str, Any], output_dir: Path) -> str:
    """Cria tabela de resultados de testes de carga (Locust)"""
    
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.axis('tight')
    ax.axis('off')
    
    headers = ["Endpoint", "Estratégia", "Requisições", "Lat. Média (ms)", 
               "Lat. Mediana (ms)", "Throughput (req/s)", "Taxa Erro"]
    
    table_data = []
    
    db_endpoints = data.get("db", {}).get("endpoints", {})
    cache_endpoints = data.get("cache", {}).get("endpoints", {})
    
    # Endpoints únicos
    all_endpoints = set(list(db_endpoints.keys()) + list(cache_endpoints.keys()))
    
    for endpoint in sorted(all_endpoints):
        db_data = db_endpoints.get(endpoint, {})
        cache_data = cache_endpoints.get(endpoint, {})
        
        # DB
        if db_data:
            table_data.append([
                endpoint,
                "DB",
                str(db_data.get("request_count", 0)),
                format_number(db_data.get("average_response_time", 0)),
                format_number(db_data.get("median_response_time", 0)),
                format_number(db_data.get("requests_per_second", 0)),
                f"{((db_data.get('failure_count', 0) / max(db_data.get('request_count', 1), 1)) * 100):.1f}%"
            ])
        
        # Cache
        if cache_data:
            table_data.append([
                endpoint,
                "Cache",
                str(cache_data.get("request_count", 0)),
                format_number(cache_data.get("average_response_time", 0)),
                format_number(cache_data.get("median_response_time", 0)),
                format_number(cache_data.get("requests_per_second", 0)),
                f"{((cache_data.get('failure_count', 0) / max(cache_data.get('request_count', 1), 1)) * 100):.1f}%"
            ])
    
    table = ax.table(
        cellText=table_data,
        colLabels=headers,
        cellLoc='center',
        loc='center',
        bbox=[0, 0, 1, 1]
    )
    
    # Estilizar cabeçalho
    for i in range(len(headers)):
        cell = table[(0, i)]
        cell.set_facecolor("#1976D2")
        cell.set_text_props(weight='bold', color='white', fontsize=16)
        cell.set_height(0.1)
    
    # Estilizar células
    for i in range(1, len(table_data) + 1):
        # Coluna de estratégia
        strategy = table_data[i-1][1]
        strategy_cell = table[(i, 1)]
        
        if strategy == "DB":
            strategy_cell.set_facecolor("#E3F2FD")
            strategy_cell.set_text_props(weight='bold', fontsize=38)
        else:
            strategy_cell.set_facecolor("#FFF3E0")
            strategy_cell.set_text_props(weight='bold', fontsize=38)
        
        # Primeira coluna (endpoint) - fundo cinza para primeira linha de cada endpoint
        if i == 1 or table_data[i-1][0] != table_data[i-2][0]:
            endpoint_cell = table[(i, 0)]
            endpoint_cell.set_facecolor("#F5F5F5")
            endpoint_cell.set_text_props(weight='bold', fontsize=38)
        
        for j in range(len(headers)):
            table[(i, j)].set_height(0.08)
    
    title = "Comparação de Desempenho sob Carga: DB vs Cache\n(Testes Locust - 10 usuários, 1 minuto)"
    fig.suptitle(title, fontsize=14, fontweight='bold', y=0.98)
    
    legend_elements = [
        mpatches.Patch(facecolor="#E3F2FD", label="Estratégia DB"),
        mpatches.Patch(facecolor="#FFF3E0", label="Estratégia Cache")
    ]
    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.05), ncol=2, fontsize=12)
    
    plt.tight_layout()
    
    output_path = output_dir / "tabela_locust_carga.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Gera tabelas bonitas em PNG a partir dos resultados dos testes"
    )
    parser.add_argument(
        "--quick",
        type=str,
        help="Caminho para arquivo JSON de comparação quick (latência individual)"
    )
    parser.add_argument(
        "--locust",
        type=str,
        help="Caminho para arquivo JSON de comparação locust (carga)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Gera todas as tabelas usando arquivos padrão"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/tables",
        help="Diretório de saída (padrão: results/tables)"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    if args.all:
        # Gerar todas as tabelas
        quick_file = Path("results/quick_comparison.json")
        locust_file = Path("results/locust_comparison.json")
        
        if quick_file.exists():
            print(f"Processando {quick_file}...")
            with open(quick_file, 'r', encoding='utf-8') as f:
                quick_data = json.load(f)
            
            print("  -> Gerando tabela de latencia (comparacao)...")
            file1 = create_quick_latency_table(quick_data, output_dir)
            generated_files.append(file1)
            print(f"    OK: {file1}")
            
            print("  -> Gerando tabela de latencia (detalhada)...")
            file2 = create_quick_detailed_table(quick_data, output_dir)
            generated_files.append(file2)
            print(f"    OK: {file2}")
        else:
            print(f"AVISO: Arquivo nao encontrado: {quick_file}")
        
        if locust_file.exists():
            print(f"Processando {locust_file}...")
            with open(locust_file, 'r', encoding='utf-8') as f:
                locust_data = json.load(f)
            
            print("  -> Gerando tabela de carga (Locust)...")
            file3 = create_locust_table(locust_data, output_dir)
            generated_files.append(file3)
            print(f"    OK: {file3}")
        else:
            print(f"AVISO: Arquivo nao encontrado: {locust_file}")
    
    elif args.quick:
        print(f"Processando {args.quick}...")
        with open(args.quick, 'r', encoding='utf-8') as f:
            quick_data = json.load(f)
        
        print("  -> Gerando tabela de latencia (comparacao)...")
        file1 = create_quick_latency_table(quick_data, output_dir)
        generated_files.append(file1)
        print(f"    OK: {file1}")
        
        print("  -> Gerando tabela de latencia (detalhada)...")
        file2 = create_quick_detailed_table(quick_data, output_dir)
        generated_files.append(file2)
        print(f"    OK: {file2}")
    
    elif args.locust:
        print(f"Processando {args.locust}...")
        with open(args.locust, 'r', encoding='utf-8') as f:
            locust_data = json.load(f)
        
        print("  -> Gerando tabela de carga (Locust)...")
        file3 = create_locust_table(locust_data, output_dir)
        generated_files.append(file3)
        print(f"    OK: {file3}")
    
    else:
        parser.print_help()
        return
    
    print(f"\nTabelas geradas com sucesso em: {output_dir}")
    print(f"Total: {len(generated_files)} arquivo(s)")


if __name__ == "__main__":
    main()
