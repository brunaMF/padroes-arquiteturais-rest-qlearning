#!/usr/bin/env python3
"""
Script para analisar e comparar resultados do Locust entre estratégias DB e Cache.
"""
import argparse
import csv
import json
import os
import statistics
from typing import Dict, List, Optional
from pathlib import Path


def read_locust_csv(csv_file: str) -> Dict:
    """
    Lê arquivo CSV do Locust e retorna métricas principais.
    
    Formato esperado: locust_results_stats.csv
    """
    if not os.path.exists(csv_file):
        print(f"❌ Arquivo não encontrado: {csv_file}")
        return None
    
    metrics = {
        "file": csv_file,
        "total_requests": 0,
        "failures": 0,
        "median_response_time": 0,
        "average_response_time": 0,
        "min_response_time": 0,
        "max_response_time": 0,
        "requests_per_second": 0,
        "endpoints": {}
    }
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                endpoint = row.get('Name', '').strip()
                type_field = row.get('Type', '').strip()
                
                # Ignorar linhas vazias ou de cabeçalho
                if not endpoint or endpoint == 'Aggregated':
                    continue
                
                # Métricas agregadas (primeira linha geralmente)
                if type_field == 'Aggregated' or endpoint == 'Total':
                    try:
                        metrics["total_requests"] = int(row.get('Request Count', 0))
                        metrics["failures"] = int(row.get('Failure Count', 0))
                        metrics["median_response_time"] = float(row.get('Median Response Time', 0))
                        metrics["average_response_time"] = float(row.get('Average Response Time', 0))
                        metrics["min_response_time"] = float(row.get('Min Response Time', 0))
                        metrics["max_response_time"] = float(row.get('Max Response Time', 0))
                        metrics["requests_per_second"] = float(row.get('Requests/s', 0))
                    except (ValueError, KeyError):
                        pass
                
                # Métricas por endpoint
                if endpoint and endpoint not in ['Total', 'Aggregated']:
                    try:
                        metrics["endpoints"][endpoint] = {
                            "request_count": int(row.get('Request Count', 0)),
                            "failure_count": int(row.get('Failure Count', 0)),
                            "median_response_time": float(row.get('Median Response Time', 0)),
                            "average_response_time": float(row.get('Average Response Time', 0)),
                            "min_response_time": float(row.get('Min Response Time', 0)),
                            "max_response_time": float(row.get('Max Response Time', 0)),
                            "requests_per_second": float(row.get('Requests/s', 0))
                        }
                    except (ValueError, KeyError):
                        pass
        
        return metrics
    except Exception as e:
        print(f"❌ Erro ao ler arquivo {csv_file}: {e}")
        return None


def calculate_percentiles(response_times: List[float]) -> Dict:
    """Calcula percentis a partir de lista de tempos de resposta"""
    if not response_times:
        return {"p50": 0, "p95": 0, "p99": 0}
    
    sorted_times = sorted(response_times)
    n = len(sorted_times)
    
    return {
        "p50": sorted_times[int(n * 0.50)] if n > 0 else 0,
        "p95": sorted_times[int(n * 0.95)] if n > 1 else sorted_times[-1],
        "p99": sorted_times[int(n * 0.99)] if n > 1 else sorted_times[-1]
    }


def read_locust_history(csv_file: str) -> Optional[Dict]:
    """
    Lê arquivo de histórico do Locust para obter percentis mais precisos.
    Formato esperado: locust_results_stats_history.csv
    """
    history_file = csv_file.replace('_stats.csv', '_stats_history.csv')
    
    if not os.path.exists(history_file):
        return None
    
    try:
        response_times = []
        with open(history_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Tentar diferentes nomes de coluna
                    rt = row.get('Average Response Time', row.get('Response Time', 0))
                    if rt:
                        response_times.append(float(rt))
                except (ValueError, KeyError):
                    pass
        
        if response_times:
            return calculate_percentiles(response_times)
    except Exception as e:
        print(f"⚠️  Não foi possível ler histórico: {e}")
    
    return None


def compare_strategies(db_file: str, cache_file: str, output_file: Optional[str] = None):
    """Compara resultados entre estratégias DB e Cache"""
    
    print("=" * 70)
    print("ANÁLISE COMPARATIVA: DB vs CACHE")
    print("=" * 70)
    
    # Ler resultados
    print("\n📊 Carregando resultados...")
    db_metrics = read_locust_csv(db_file)
    cache_metrics = read_locust_csv(cache_file)
    
    if not db_metrics:
        print(f"❌ Não foi possível carregar resultados de DB: {db_file}")
        return
    
    if not cache_metrics:
        print(f"❌ Não foi possível carregar resultados de Cache: {cache_file}")
        return
    
    # Comparação geral
    print("\n" + "=" * 70)
    print("MÉTRICAS GERAIS")
    print("=" * 70)
    
    comparison = {
        "db": db_metrics,
        "cache": cache_metrics,
        "comparison": {}
    }
    
    # Calcular diferenças percentuais
    metrics_to_compare = [
        ("average_response_time", "Latência Média (ms)"),
        ("median_response_time", "Latência Mediana (ms)"),
        ("max_response_time", "Latência Máxima (ms)"),
        ("requests_per_second", "Throughput (req/s)"),
        ("failures", "Falhas"),
        ("total_requests", "Total de Requisições")
    ]
    
    print(f"\n{'Métrica':<30} {'DB':<15} {'Cache':<15} {'Diferença':<15}")
    print("-" * 70)
    
    for metric_key, metric_name in metrics_to_compare:
        db_value = db_metrics.get(metric_key, 0)
        cache_value = cache_metrics.get(metric_key, 0)
        
        if db_value == 0:
            diff_pct = 0
        else:
            diff_pct = ((cache_value - db_value) / db_value) * 100
        
        comparison["comparison"][metric_key] = {
            "db": db_value,
            "cache": cache_value,
            "difference_percent": diff_pct
        }
        
        # Formatação
        if metric_key in ["average_response_time", "median_response_time", "max_response_time"]:
            db_str = f"{db_value:.2f} ms"
            cache_str = f"{cache_value:.2f} ms"
        elif metric_key == "requests_per_second":
            db_str = f"{db_value:.2f} req/s"
            cache_str = f"{cache_value:.2f} req/s"
        else:
            db_str = f"{int(db_value)}"
            cache_str = f"{int(cache_value)}"
        
        diff_str = f"{diff_pct:+.1f}%"
        if diff_pct < 0:
            diff_str = f"{diff_str} (Cache mais rápido)"
        elif diff_pct > 0:
            diff_str = f"{diff_str} (DB mais rápido)"
        else:
            diff_str = "0% (igual)"
        
        print(f"{metric_name:<30} {db_str:<15} {cache_str:<15} {diff_str:<15}")
    
    # Comparação por endpoint
    print("\n" + "=" * 70)
    print("MÉTRICAS POR ENDPOINT")
    print("=" * 70)
    
    all_endpoints = set(db_metrics.get("endpoints", {}).keys()) | set(cache_metrics.get("endpoints", {}).keys())
    
    if all_endpoints:
        print(f"\n{'Endpoint':<40} {'DB (ms)':<15} {'Cache (ms)':<15} {'Diferença':<15}")
        print("-" * 70)
        
        for endpoint in sorted(all_endpoints):
            db_endpoint = db_metrics.get("endpoints", {}).get(endpoint, {})
            cache_endpoint = cache_metrics.get("endpoints", {}).get(endpoint, {})
            
            db_avg = db_endpoint.get("average_response_time", 0)
            cache_avg = cache_endpoint.get("average_response_time", 0)
            
            if db_avg == 0:
                diff_pct = 0
            else:
                diff_pct = ((cache_avg - db_avg) / db_avg) * 100
            
            diff_str = f"{diff_pct:+.1f}%"
            if diff_pct < 0:
                diff_str = f"{diff_str} (Cache mais rápido)"
            elif diff_pct > 0:
                diff_str = f"{diff_str} (DB mais rápido)"
            
            print(f"{endpoint:<40} {db_avg:<15.2f} {cache_avg:<15.2f} {diff_str:<15}")
    
    # Taxa de erro
    print("\n" + "=" * 70)
    print("TAXA DE ERRO")
    print("=" * 70)
    
    db_total = db_metrics.get("total_requests", 1)
    db_failures = db_metrics.get("failures", 0)
    db_error_rate = (db_failures / db_total * 100) if db_total > 0 else 0
    
    cache_total = cache_metrics.get("total_requests", 1)
    cache_failures = cache_metrics.get("failures", 0)
    cache_error_rate = (cache_failures / cache_total * 100) if cache_total > 0 else 0
    
    print(f"\nDB:   {db_failures}/{db_total} falhas ({db_error_rate:.2f}%)")
    print(f"Cache: {cache_failures}/{cache_total} falhas ({cache_error_rate:.2f}%)")
    
    comparison["comparison"]["error_rate"] = {
        "db": db_error_rate,
        "cache": cache_error_rate,
        "difference_percent": cache_error_rate - db_error_rate
    }
    
    # Conclusão
    print("\n" + "=" * 70)
    print("CONCLUSÃO")
    print("=" * 70)
    
    avg_diff = comparison["comparison"]["average_response_time"]["difference_percent"]
    throughput_diff = comparison["comparison"]["requests_per_second"]["difference_percent"]
    
    print("\n📈 Análise:")
    if avg_diff < -10:
        print("✅ Cache é SIGNIFICATIVAMENTE mais rápido que DB")
        print(f"   → Cache é {abs(avg_diff):.1f}% mais rápido em latência média")
    elif avg_diff < -5:
        print("✅ Cache é mais rápido que DB")
        print(f"   → Cache é {abs(avg_diff):.1f}% mais rápido em latência média")
    elif avg_diff > 10:
        print("✅ DB é SIGNIFICATIVAMENTE mais rápido que Cache")
        print(f"   → DB é {abs(avg_diff):.1f}% mais rápido em latência média")
    elif avg_diff > 5:
        print("✅ DB é mais rápido que Cache")
        print(f"   → DB é {abs(avg_diff):.1f}% mais rápido em latência média")
    else:
        print("⚠️  Diferença de desempenho é MARGINAL (< 5%)")
        print("   → Ambas estratégias têm desempenho similar")
    
    if throughput_diff > 10:
        print(f"\n📊 Throughput: Cache processa {abs(throughput_diff):.1f}% mais requisições/segundo")
    elif throughput_diff < -10:
        print(f"\n📊 Throughput: DB processa {abs(throughput_diff):.1f}% mais requisições/segundo")
    
    # Salvar resultados
    if output_file:
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Resultados salvos em: {output_file}")
    
    return comparison


def main():
    parser = argparse.ArgumentParser(description="Analisa e compara resultados do Locust")
    parser.add_argument("--db", required=True, help="Arquivo CSV do Locust para estratégia DB")
    parser.add_argument("--cache", required=True, help="Arquivo CSV do Locust para estratégia Cache")
    parser.add_argument("--output", default="results/locust_comparison.json", help="Arquivo de saída JSON")
    
    args = parser.parse_args()
    
    # Verificar se arquivos existem
    if not os.path.exists(args.db):
        print(f"❌ Arquivo DB não encontrado: {args.db}")
        print("   Certifique-se de executar Locust com --csv=results/locust/locust_db_results")
        return
    
    if not os.path.exists(args.cache):
        print(f"❌ Arquivo Cache não encontrado: {args.cache}")
        print("   Certifique-se de executar Locust com --csv=results/locust/locust_cache_results")
        return
    
    compare_strategies(args.db, args.cache, args.output)


if __name__ == "__main__":
    main()
