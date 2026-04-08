import time
import requests
import statistics
import subprocess
import sys
import json
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal
import os
from contextlib import contextmanager

class APIBenchmark:
    def __init__(self, fastapi_url="http://127.0.0.1:8000", flask_url="http://127.0.0.1:5000"):
        self.fastapi_url = fastapi_url
        self.flask_url = flask_url
        self.results = {
            "fastapi": {},
            "flask": {}
        }
        
        # Test data
        self.test_item = {
            "name": "Test Product",
            "price": 99.99,
            "quantity": 10,
            "tags": ["test", "benchmark"]
        }
        
        self.invalid_item = {
            "name": "",  # Invalid: empty name
            "price": -10,  # Invalid: negative price
            "quantity": 5000  # Invalid: exceeds max
        }
    
    def measure_endpoint(self, url: str, method: str = "GET", 
                        data: dict = None, iterations: int = 100) -> Dict:
        """Measure performance of a single endpoint"""
        times = []
        status_codes = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            try:
                if method == "GET":
                    response = requests.get(url, timeout=5)
                elif method == "POST":
                    response = requests.post(url, json=data, timeout=5)
                elif method == "PUT":
                    response = requests.put(url, json=data, timeout=5)
                elif method == "DELETE":
                    response = requests.delete(url, timeout=5)
                
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)  # Convert to ms
                status_codes.append(response.status_code)
            except Exception as e:
                print(f"Error measuring {url}: {e}")
                times.append(float('inf'))
                status_codes.append(0)
        
        # Remove failed requests from timing
        valid_times = [t for t, code in zip(times, status_codes) if code == 200]
        
        if not valid_times:
            return {
                "error": "All requests failed",
                "success_rate": 0
            }
        
        return {
            "min": min(valid_times),
            "max": max(valid_times),
            "mean": statistics.mean(valid_times),
            "median": statistics.median(valid_times),
            "std_dev": statistics.stdev(valid_times) if len(valid_times) > 1 else 0,
            "success_rate": len(valid_times) / iterations * 100,
            "total_requests": iterations
        }
    
    def run_concurrent_test(self, url: str, method: str = "GET", 
                           data: dict = None, concurrent_users: int = 10, 
                           requests_per_user: int = 10) -> Dict:
        """Test concurrent performance"""
        def make_request():
            start_time = time.perf_counter()
            try:
                if method == "GET":
                    response = requests.get(url, timeout=5)
                elif method == "POST":
                    response = requests.post(url, json=data, timeout=5)
                
                end_time = time.perf_counter()
                return (end_time - start_time) * 1000, response.status_code == 200
            except:
                return float('inf'), False
        
        all_times = []
        successful_requests = 0
        total_requests = concurrent_users * requests_per_user
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for _ in range(total_requests):
                futures.append(executor.submit(make_request))
            
            for future in as_completed(futures):
                time_taken, success = future.result()
                if success:
                    all_times.append(time_taken)
                    successful_requests += 1
        
        if not all_times:
            return {"error": "All requests failed"}
        
        return {
            "mean": statistics.mean(all_times),
            "median": statistics.median(all_times),
            "throughput": successful_requests / (sum(all_times) / 1000),  # requests per second
            "success_rate": successful_requests / total_requests * 100,
            "total_successful": successful_requests,
            "total_requests": total_requests
        }
    
    def benchmark_get_root(self):
        """Benchmark root endpoint"""
        print("\n📊 Benchmarking GET / endpoint...")
        
        fastapi_results = self.measure_endpoint(f"{self.fastapi_url}/")
        flask_results = self.measure_endpoint(f"{self.flask_url}/")
        
        self.results["fastapi"]["root"] = fastapi_results
        self.results["flask"]["root"] = flask_results
        
        return fastapi_results, flask_results
    
    def benchmark_create_item(self):
        """Benchmark POST /items/ endpoint"""
        print("\n📊 Benchmarking POST /items/ (with validation)...")
        
        fastapi_results = self.measure_endpoint(
            f"{self.fastapi_url}/items/", 
            method="POST", 
            data=self.test_item
        )
        
        flask_results = self.measure_endpoint(
            f"{self.flask_url}/items/", 
            method="POST", 
            data=self.test_item
        )
        
        self.results["fastapi"]["create"] = fastapi_results
        self.results["flask"]["create"] = flask_results
        
        return fastapi_results, flask_results
    
    def benchmark_get_items(self):
        """Benchmark GET /items/ endpoint"""
        print("\n📊 Benchmarking GET /items/ with pagination...")
        
        fastapi_results = self.measure_endpoint(
            f"{self.fastapi_url}/items/?skip=0&limit=50"
        )
        
        flask_results = self.measure_endpoint(
            f"{self.flask_url}/items/?skip=0&limit=50"
        )
        
        self.results["fastapi"]["list"] = fastapi_results
        self.results["flask"]["list"] = flask_results
        
        return fastapi_results, flask_results
    
    def benchmark_concurrent_requests(self):
        """Benchmark concurrent request handling"""
        print("\n📊 Benchmarking concurrent requests (10 users, 10 requests each)...")
        
        fastapi_results = self.run_concurrent_test(
            f"{self.fastapi_url}/items/",
            concurrent_users=10,
            requests_per_user=10
        )
        
        flask_results = self.run_concurrent_test(
            f"{self.flask_url}/items/",
            concurrent_users=10,
            requests_per_user=10
        )
        
        self.results["fastapi"]["concurrent"] = fastapi_results
        self.results["flask"]["concurrent"] = flask_results
        
        return fastapi_results, flask_results
    
    def print_comparison(self):
        """Print formatted comparison results"""
        print("\n" + "="*80)
        print("🚀 FASTAPI vs FLASK PERFORMANCE COMPARISON")
        print("="*80)
        
        endpoints = [
            ("GET /", "root"),
            ("POST /items/", "create"),
            ("GET /items/", "list")
        ]
        
        print(f"\n{'Endpoint':<20} {'Framework':<10} {'Mean (ms)':<12} {'Median (ms)':<12} {'Success Rate':<12}")
        print("-"*80)
        
        for endpoint_name, key in endpoints:
            for framework in ["fastapi", "flask"]:
                if key in self.results[framework] and "error" not in self.results[framework][key]:
                    data = self.results[framework][key]
                    print(f"{endpoint_name:<20} {framework.upper():<10} "
                          f"{data['mean']:<12.2f} {data['median']:<12.2f} "
                          f"{data['success_rate']:<12.1f}%")
            print()
        
        # Concurrent results
        print(f"\n{'Concurrent Test':<20} {'Framework':<10} {'Mean (ms)':<12} {'Throughput':<15} {'Success Rate':<12}")
        print("-"*80)
        
        for framework in ["fastapi", "flask"]:
            if "concurrent" in self.results[framework] and "error" not in self.results[framework]["concurrent"]:
                data = self.results[framework]["concurrent"]
                print(f"{'10 users x 10 req':<20} {framework.upper():<10} "
                      f"{data['mean']:<12.2f} {data['throughput']:<15.2f} req/s "
                      f"{data['success_rate']:<12.1f}%")
        
        # Calculate performance advantage
        print("\n" + "="*80)
        print("📈 PERFORMANCE ANALYSIS")
        print("="*80)
        
        for endpoint_name, key in endpoints:
            if key in self.results["fastapi"] and key in self.results["flask"]:
                if "error" not in self.results["fastapi"][key] and "error" not in self.results["flask"][key]:
                    fastapi_mean = self.results["fastapi"][key]["mean"]
                    flask_mean = self.results["flask"][key]["mean"]
                    
                    if flask_mean > 0:
                        speedup = (flask_mean - fastapi_mean) / flask_mean * 100
                        faster = "faster" if speedup > 0 else "slower"
                        print(f"\n{endpoint_name}:")
                        print(f"  FastAPI is {abs(speedup):.1f}% {faster} than Flask")
                        print(f"  FastAPI: {fastapi_mean:.2f}ms | Flask: {flask_mean:.2f}ms")
        
        # Concurrent performance advantage
        if "concurrent" in self.results["fastapi"] and "concurrent" in self.results["flask"]:
            if "error" not in self.results["fastapi"]["concurrent"] and "error" not in self.results["flask"]["concurrent"]:
                fastapi_tput = self.results["fastapi"]["concurrent"]["throughput"]
                flask_tput = self.results["flask"]["concurrent"]["throughput"]
                
                if flask_tput > 0:
                    tput_increase = (fastapi_tput - flask_tput) / flask_tput * 100
                    print(f"\nConcurrent Performance:")
                    print(f"  FastAPI handles {tput_increase:.1f}% more requests per second")
                    print(f"  FastAPI: {fastapi_tput:.2f} req/s | Flask: {flask_tput:.2f} req/s")
    
    def create_visualization(self):
        """Create performance comparison charts"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('FastAPI vs Flask Performance Comparison', fontsize=16, fontweight='bold')
        
        # Bar chart for mean response times
        ax1 = axes[0, 0]
        endpoints = ['GET /', 'POST /items/', 'GET /items/']
        fastapi_means = []
        flask_means = []
        
        for key in ['root', 'create', 'list']:
            if key in self.results['fastapi'] and 'mean' in self.results['fastapi'][key]:
                fastapi_means.append(self.results['fastapi'][key]['mean'])
            else:
                fastapi_means.append(0)
            
            if key in self.results['flask'] and 'mean' in self.results['flask'][key]:
                flask_means.append(self.results['flask'][key]['mean'])
            else:
                flask_means.append(0)
        
        x = np.arange(len(endpoints))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, fastapi_means, width, label='FastAPI', color='#009688')
        bars2 = ax1.bar(x + width/2, flask_means, width, label='Flask', color='#FF5722')
        
        ax1.set_ylabel('Response Time (ms)')
        ax1.set_title('Mean Response Time Comparison')
        ax1.set_xticks(x)
        ax1.set_xticklabels(endpoints)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}', ha='center', va='bottom', fontsize=8)
        
        # Concurrent throughput comparison
        ax2 = axes[0, 1]
        if 'concurrent' in self.results['fastapi'] and 'concurrent' in self.results['flask']:
            frameworks = ['FastAPI', 'Flask']
            throughputs = [
                self.results['fastapi']['concurrent'].get('throughput', 0),
                self.results['flask']['concurrent'].get('throughput', 0)
            ]
            
            bars = ax2.bar(frameworks, throughputs, color=['#009688', '#FF5722'])
            ax2.set_ylabel('Requests per Second')
            ax2.set_title('Concurrent Request Throughput\n(10 users, 100 total requests)')
            ax2.grid(True, alpha=0.3)
            
            for bar, tput in zip(bars, throughputs):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{tput:.1f}', ha='center', va='bottom')
        
        # Success rate comparison
        ax3 = axes[1, 0]
        success_rates = {
            'FastAPI': [],
            'Flask': []
        }
        
        for key in ['root', 'create', 'list']:
            for framework, label in [('fastapi', 'FastAPI'), ('flask', 'Flask')]:
                if key in self.results[framework] and 'success_rate' in self.results[framework][key]:
                    success_rates[label].append(self.results[framework][key]['success_rate'])
                else:
                    success_rates[label].append(0)
        
        x = np.arange(len(endpoints))
        
        ax3.plot(x, success_rates['FastAPI'], marker='o', label='FastAPI', 
                color='#009688', linewidth=2, markersize=8)
        ax3.plot(x, success_rates['Flask'], marker='s', label='Flask', 
                color='#FF5722', linewidth=2, markersize=8)
        
        ax3.set_ylabel('Success Rate (%)')
        ax3.set_title('Request Success Rate')
        ax3.set_xticks(x)
        ax3.set_xticklabels(endpoints)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim([95, 105])
        
        # Response time distribution (box plot style)
        ax4 = axes[1, 1]
        ax4.axis('off')
        
        # Summary text
        summary_text = "KEY FASTAPI ADVANTAGES:\n\n"
        summary_text += "✓ Automatic request validation\n"
        summary_text += "✓ Interactive API documentation (/docs)\n"
        summary_text += "✓ Async support built-in\n"
        summary_text += "✓ Type hints for better IDE support\n"
        summary_text += "✓ Less boilerplate code\n"
        summary_text += "✓ Automatic JSON Schema generation\n"
        summary_text += "✓ Dependency injection system\n"
        summary_text += "✓ WebSocket support out of the box\n\n"
        
        if 'concurrent' in self.results['fastapi'] and 'concurrent' in self.results['flask']:
            fastapi_tput = self.results['fastapi']['concurrent'].get('throughput', 0)
            flask_tput = self.results['flask']['concurrent'].get('throughput', 0)
            if flask_tput > 0:
                improvement = ((fastapi_tput - flask_tput) / flask_tput) * 100
                summary_text += f"PERFORMANCE IMPROVEMENT:\n"
                summary_text += f"→ {improvement:.1f}% higher throughput with FastAPI\n"
        
        ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes, fontsize=11,
                verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        plt.savefig('benchmark_results.png', dpi=100, bbox_inches='tight')
        print("\n📊 Visualization saved as 'benchmark_results.png'")
        plt.show()

def check_servers_running(fastapi_url="http://127.0.0.1:8000", flask_url="http://127.0.0.1:5000"):
    """Check if both servers are running"""
    print("🔍 Checking if servers are running...")
    
    fastapi_ok = False
    flask_ok = False
    
    try:
        response = requests.get(f"{fastapi_url}/health", timeout=2)
        fastapi_ok = response.status_code == 200
        print(f"  FastAPI: {'✓ Running' if fastapi_ok else '✗ Not responding'}")
    except:
        print("  FastAPI: ✗ Not running")
    
    try:
        response = requests.get(f"{flask_url}/health", timeout=2)
        flask_ok = response.status_code == 200
        print(f"  Flask: {'✓ Running' if flask_ok else '✗ Not responding'}")
    except:
        print("  Flask: ✗ Not running")
    
    if not (fastapi_ok and flask_ok):
        print("\n❌ Error: Both servers must be running!")
        print("\nPlease start the servers in separate terminals:")
        print("  Terminal 1: python fastapi_app.py")
        print("  Terminal 2: python flask_app.py")
        print("\nThen run this benchmark again.")
        return False
    
    print("\n✓ Both servers are running!")
    return True

def main():
    """Main benchmark function"""
    print("="*80)
    print("🚀 FASTAPI vs FLASK BENCHMARK TOOL")
    print("="*80)
    
    if not check_servers_running():
        sys.exit(1)
    
    # Initialize benchmark
    benchmark = APIBenchmark()
    
    # Run benchmarks
    print("\n" + "="*80)
    print("📊 RUNNING BENCHMARKS")
    print("="*80)
    
    benchmark.benchmark_get_root()
    benchmark.benchmark_create_item()
    benchmark.benchmark_get_items()
    benchmark.benchmark_concurrent_requests()
    
    # Print results
    benchmark.print_comparison()
    
    # Create visualization
    print("\n" + "="*80)
    print("📈 CREATING VISUALIZATION")
    print("="*80)
    benchmark.create_visualization()
    
    # Save results to JSON
    with open('benchmark_results.json', 'w') as f:
        json.dump(benchmark.results, f, indent=2)
    print("\n📁 Results saved to 'benchmark_results.json'")
    
    print("\n" + "="*80)
    print("✅ BENCHMARK COMPLETE!")
    print("="*80)
    print("\n💡 FastAPI Key Advantages Demonstrated:")
    print("  1. Built-in validation (Pydantic models)")
    print("  2. Automatic interactive docs at /docs")
    print("  3. Async support for better performance")
    print("  4. Type hints for fewer bugs")
    print("  5. Less boilerplate code")
    print("\n📖 Check out the automatic API documentation at:")
    print("  - FastAPI: http://127.0.0.1:8000/docs")
    print("  - FastAPI ReDoc: http://127.0.0.1:8000/redoc")

if __name__ == "__main__":
    main()