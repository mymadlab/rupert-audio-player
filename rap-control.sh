#!/usr/bin/env bash
set -euo pipefail

ACTION="${1:-}"

# Allow all deployment-specific values to be overridden from the unit file.
APP_DIR="${APP_DIR:-/home/rupert/app/bin}"
PYTHON_BIN="${PYTHON_BIN:-/home/rupert/app/rupert_venv-0.0.1/bin/python}"
RAP_SCRIPT="${RAP_SCRIPT:-${APP_DIR}/rap.py}"
RAP_TOPIC="${RAP_TOPIC:-rupert.audio.control}"
RUPERT_CONFIG_PATH="${RUPERT_CONFIG_PATH:-${APP_DIR}/rupert_config.json}"
RUPERT_PROSUMER_PATH="${RUPERT_PROSUMER_PATH:-}"

# Used by status/stop to discover the RAP process.
PROCESS_MATCH="${PROCESS_MATCH:-${RAP_SCRIPT} ${RAP_TOPIC}}"

usage() {
	echo "Usage: $0 {start|stop|restart|status}"
}

require_files() {
	if [[ ! -x "${PYTHON_BIN}" ]]; then
		echo "Error: Python interpreter not executable: ${PYTHON_BIN}" >&2
		exit 1
	fi
	if [[ ! -f "${RAP_SCRIPT}" ]]; then
		echo "Error: RAP script not found: ${RAP_SCRIPT}" >&2
		exit 1
	fi
	if [[ ! -f "${RUPERT_CONFIG_PATH}" ]]; then
		echo "Error: Config file not found: ${RUPERT_CONFIG_PATH}" >&2
		exit 1
	fi
}

start_service() {
	require_files
	export RUPERT_CONFIG_PATH

	if [[ -n "${RUPERT_PROSUMER_PATH}" ]]; then
		export PYTHONPATH="${RUPERT_PROSUMER_PATH}:${PYTHONPATH:-}"
	fi

	# For systemd Type=simple, this process must stay in the foreground.
	exec "${PYTHON_BIN}" "${RAP_SCRIPT}" "${RAP_TOPIC}"
}

stop_service() {
	if pgrep -f "${PROCESS_MATCH}" >/dev/null 2>&1; then
		pkill -TERM -f "${PROCESS_MATCH}"
		echo "Stopped RAP process matching: ${PROCESS_MATCH}"
	else
		echo "RAP is not running"
	fi
}

status_service() {
	if pgrep -fa "${PROCESS_MATCH}" >/dev/null 2>&1; then
		echo "RAP is running"
		pgrep -fa "${PROCESS_MATCH}"
	else
		echo "RAP is not running"
		exit 3
	fi
}

restart_service() {
	stop_service || true
	start_service
}

case "${ACTION}" in
	start)
		start_service
		;;
	stop)
		stop_service
		;;
	restart)
		restart_service
		;;
	status)
		status_service
		;;
	*)
		usage
		exit 1
		;;
esac
