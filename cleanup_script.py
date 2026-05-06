import os
import glob
import subprocess

files_to_remove = [
    "generate_postgres_report.py", "generate_sqlite_report.py", "generate_test_report.py",
    "load_test_report.pdf", "metrics_log.jsonl", "latency_per_endpoint.png", 
    "throughput_over_time.png", "throughput_per_endpoint.png", "precommit_log.json",
    "pre-commit_logs.py", "send_precommit_log.py", "locustfile.py", "run_load_test.py",
    "status_monitor.py", "system_status.py", "engineering_monitor.py", "functionality_monitor.py",
    "rnf_monitor.py", "technology_monitor.py", "demo_dashboard.py", "main_mongo.py",
    "main_simple.py", "models_mongo.py", "app/models_mongo.py", "pre_criacao_usuarios.py",
    "create_test_user.py", "init_test_users.py", "login_debug.py", "test_postgres.py",
    "test_server.py", "mqtt_test.py", "mqtt_subscriber.py", "smoke.py", "models_mongo.py"
]

patterns_to_remove = [
    "load_test_results*.csv", "load_test_results*.jsonl", "error_rate*.png",
    "bandit_output*.txt", "*_test_report.pdf", "*_test_results.json", "locust_*.py"
]

for p in patterns_to_remove:
    files_to_remove.extend(glob.glob(p))

for f in files_to_remove:
    if os.path.exists(f):
        subprocess.run(["git", "rm", "-f", f])

os.makedirs("scripts/startup", exist_ok=True)
startup_scripts = ["run.bat", "run.sh", "start.bat", "start_system.bat", "start_system.py", "start-docker.ps1", "start-docker.sh"]
for s in startup_scripts:
    if os.path.exists(s):
        subprocess.run(["git", "mv", s, f"scripts/startup/{s}"])

subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "refactor: apply dead code elimination and organize root directory"])
