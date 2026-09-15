#!/usr/bin/env python3
"""
Script para analisar e comparar resultados dos testes.
"""
import argparse
import json
import os
from typing import Dict, List


def load_results(file_path: str) -> Dict:
    """Carrega resultados de um arquivo JSON"""
    with open(file_path, 'r') as f:
        return json.load(f)


def compare_latency(bd_results: Dict, cache_results: Dict) -> Dict:
    """Compara latência entre estratégias"""
    comparison = {}
    
    for endpoint in ["get_recommendation", "post_feedback", "get_stats"]:
        if endpoint in bd_results.get("endpoints", {}) and endpoint in cache_results.get("endpoints", {}):
            bd = bd_results["endpoints"][endpoint]
            cache = cache_results["endpoints"][endpoint]
            
            comparison[endpoint] = {
                "metric": ["mean", "p95", "p99"],
                "bd": [bd["mean"], bd["p95"], bd["p99"]],
                "cache": [cache["mean"], cache["p95"], cache["p99"]],
                "difference_pct": [
                    ((cache_val - bd_val) / bd_val) * 100
                    for bd_val, cache_val in zip(
                        [bd["mean"], bd["p95"], bd["p99"]],
                        [cache["mean"], cache["p95"], cache["p99"]]
                    )
                ]
            }
    
    return comparison


def generate_report(bd_file: str, cache_file: str, output_file: str):
    """Gera relatório comparativo"""
    print("=" * 70)
    print("ANÁLISE COMPARATIVA: DB vs CACHE (Testes Quick)")
    print("=" * 70)
    
    print("\n📊 Carregando resultados...")
    bd_results = load_results(bd_file)
    cache_results = load_results(cache_file)
    
    print("🔍 Comparando resultados...")
    comparison = compare_latency(bd_results, cache_results)
    
    print("\n" + "="*70)
    print("RELATÓRIO COMPARATIVO - LATÊNCIA POR ENDPOINT")
    print("="*70)
    
    # Mapear nomes de endpoints para nomes legíveis
    endpoint_names = {
        "get_recommendation": "GET /recommendations/{user_id}",
        "post_feedback": "POST /recommendations/feedback",
        "get_stats": "GET /recommendations/stats/{user_id}"
    }
    
    for endpoint, data in comparison.items():
        endpoint_name = endpoint_names.get(endpoint, endpoint.upper())
        print(f"\n{endpoint_name}:")
        print(f"  {'Métrica':<10} {'DB (ms)':<15} {'Cache (ms)':<15} {'Diferença':<15}")
        print(f"  {'-'*10} {'-'*15} {'-'*15} {'-'*15}")
        
        metric_names = {
            "mean": "Média",
            "p95": "p95",
            "p99": "p99"
        }
        
        for i, metric in enumerate(data["metric"]):
            bd_val = data["bd"][i]
            cache_val = data["cache"][i]
            diff = data["difference_pct"][i]
            
            metric_name = metric_names.get(metric, metric)
            diff_str = f"{diff:+.1f}%"
            if diff < -10:
                diff_str = f"{diff_str} (Cache muito mais rápido)"
            elif diff < -5:
                diff_str = f"{diff_str} (Cache mais rápido)"
            elif diff > 10:
                diff_str = f"{diff_str} (DB muito mais rápido)"
            elif diff > 5:
                diff_str = f"{diff_str} (DB mais rápido)"
            else:
                diff_str = f"{diff_str} (similar)"
            
            print(f"  {metric_name:<10} {bd_val:<15.2f} {cache_val:<15.2f} {diff_str:<15}")
    
    # Resumo geral
    print("\n" + "="*70)
    print("RESUMO GERAL")
    print("="*70)
    
    avg_diffs = []
    for endpoint, data in comparison.items():
        avg_diffs.append(data["difference_pct"][0])  # mean
    
    if avg_diffs:
        overall_avg = sum(avg_diffs) / len(avg_diffs)
        print(f"\n📈 Diferença média de latência: {overall_avg:+.1f}%")
        
        if overall_avg < -10:
            print("✅ Cache é SIGNIFICATIVAMENTE mais rápido que DB")
            print(f"   → Cache é em média {abs(overall_avg):.1f}% mais rápido")
        elif overall_avg < -5:
            print("✅ Cache é mais rápido que DB")
            print(f"   → Cache é em média {abs(overall_avg):.1f}% mais rápido")
        elif overall_avg > 10:
            print("✅ DB é SIGNIFICATIVAMENTE mais rápido que Cache")
            print(f"   → DB é em média {abs(overall_avg):.1f}% mais rápido")
        elif overall_avg > 5:
            print("✅ DB é mais rápido que Cache")
            print(f"   → DB é em média {abs(overall_avg):.1f}% mais rápido")
        else:
            print("⚠️  Diferença de desempenho é MARGINAL (< 5%)")
            print("   → Ambas estratégias têm desempenho similar")
    
    # Taxa de sucesso
    print("\n" + "="*70)
    print("TAXA DE SUCESSO")
    print("="*70)
    
    for endpoint, data in comparison.items():
        endpoint_name = endpoint_names.get(endpoint, endpoint)
        bd_endpoint = bd_results.get("endpoints", {}).get(endpoint, {})
        cache_endpoint = cache_results.get("endpoints", {}).get(endpoint, {})
        
        bd_success = bd_endpoint.get("success_rate", 100)
        cache_success = cache_endpoint.get("success_rate", 100)
        
        print(f"\n{endpoint_name}:")
        print(f"  DB:   {bd_success:.1f}%")
        print(f"  Cache: {cache_success:.1f}%")
    
    # Salvar relatório
    report = {
        "bd_results": bd_results,
        "cache_results": cache_results,
        "comparison": comparison,
        "summary": {
            "average_difference_percent": overall_avg if avg_diffs else 0
        }
    }
    
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Relatório salvo em: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Analisa resultados dos testes")
    parser.add_argument("--bd", default="results/latency/db_quick.json", help="Arquivo de resultados BD")
    parser.add_argument("--cache", default="results/latency/cache_quick.json", help="Arquivo de resultados Cache")
    parser.add_argument("--output", default="results/comparison_report.json", help="Arquivo de saída")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.bd):
        print(f"Erro: Arquivo não encontrado: {args.bd}")
        return
    
    if not os.path.exists(args.cache):
        print(f"Erro: Arquivo não encontrado: {args.cache}")
        return
    
    generate_report(args.bd, args.cache, args.output)


if __name__ == "__main__":
    main()