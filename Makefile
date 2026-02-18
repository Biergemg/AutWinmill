.PHONY: install load-test stress-test soak-test test-multitenant test-resilience test-security report clean

install:
	pip install locust pytest pandas requests

load-test:
	@echo "Running Load Test (10 users, 30s)..."
	locust -f tests/load/locustfile.py --headless -u 10 -r 2 --run-time 30s --csv ops/benchmarks/results/load_run
	python ops/benchmarks/generate_report.py

stress-test:
	@echo "Running Stress Test..."
	python tests/load/stress_test.py

soak-test:
	@echo "Running Soak Test..."
	python tests/load/soak_test.py

test-multitenant:
	@echo "Running Multi-tenant Isolation Test..."
	pytest tests/multitenant/test_isolation.py

test-resilience:
	@echo "Running Resilience/Chaos Test..."
	pytest tests/resilience/test_chaos.py

test-security:
	@echo "Running Security Smoke Test..."
	pytest tests/security/test_smoke.py

report:
	python ops/benchmarks/generate_report.py

clean:
	rm -f ops/benchmarks/results/*.csv
	rm -f ops/benchmarks/results/*.md
	rm -f ops/benchmarks/results/*.json
