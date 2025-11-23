#!/bin/bash
#
# Kafka Test Runner Script
# ========================
# Script để chạy các Kafka tests một cách dễ dàng
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
KAFKA_BROKER="localhost:9092"

print_header() {
    echo -e "${BLUE}"
    echo "======================================================================"
    echo "  $1"
    echo "======================================================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_kafka_running() {
    print_info "Checking if Kafka is running..."

    if docker ps | grep -q "kafka"; then
        print_success "Kafka container is running"
        return 0
    else
        print_error "Kafka container is not running"
        print_warning "Please start Kafka first:"
        echo "  cd $SCRIPT_DIR"
        echo "  docker-compose up -d"
        return 1
    fi
}

check_python_dependencies() {
    print_info "Checking Python dependencies..."

    if python -c "import confluent_kafka" 2>/dev/null; then
        print_success "confluent-kafka is installed"
        return 0
    else
        print_error "confluent-kafka is not installed"
        print_warning "Please install dependencies:"
        echo "  pip install -r $SCRIPT_DIR/requirements.txt"
        return 1
    fi
}

start_kafka() {
    print_header "Starting Kafka Server"
    cd "$SCRIPT_DIR"
    docker-compose up -d

    print_info "Waiting for Kafka to be ready..."
    sleep 5

    if check_kafka_running; then
        print_success "Kafka started successfully"
        print_info "Kafka UI: http://localhost:8080"
    else
        print_error "Failed to start Kafka"
        exit 1
    fi
}

stop_kafka() {
    print_header "Stopping Kafka Server"
    cd "$SCRIPT_DIR"
    docker-compose down
    print_success "Kafka stopped"
}

show_kafka_logs() {
    print_header "Kafka Logs"
    cd "$SCRIPT_DIR"
    docker-compose logs -f kafka
}

run_producer() {
    print_header "Running Kafka Producer Test"
    print_info "Producer Script: kafka_producer.py"
    print_info "Note: Producer does NOT require group.id"
    echo ""

    cd "$SCRIPT_DIR"
    python kafka_producer.py
}

run_consumer() {
    print_header "Running Kafka Consumer Test"
    print_info "Consumer Script: kafka_consumer_test.py"
    print_info "Note: Consumer REQUIRES group.id"
    echo ""

    cd "$SCRIPT_DIR"
    python kafka_consumer_test.py
}

run_connection_test() {
    print_header "Running Full Connection Test"
    print_info "This will test both Producer and Consumer"
    print_info "Verifying that group.id is required for Consumer"
    echo ""

    cd "$SCRIPT_DIR"
    python test_kafka_connection.py
}

show_status() {
    print_header "Kafka Server Status"

    echo "Docker Containers:"
    docker ps --filter "name=kafka" --filter "name=zookeeper" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    echo ""
    echo "Connection Info:"
    echo "  Kafka Broker: $KAFKA_BROKER"
    echo "  Kafka UI: http://localhost:8080"
    echo "  Zookeeper: localhost:2181"
}

show_menu() {
    print_header "VRecommendation - Kafka Test Runner"

    echo "1. Start Kafka Server"
    echo "2. Stop Kafka Server"
    echo "3. Show Kafka Status"
    echo "4. Show Kafka Logs"
    echo ""
    echo "5. Run Connection Test (Full Test Suite)"
    echo "6. Run Producer Test"
    echo "7. Run Consumer Test"
    echo ""
    echo "8. Open Kafka UI"
    echo "9. Exit"
    echo ""
}

open_kafka_ui() {
    print_info "Opening Kafka UI in browser..."

    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8080
    elif command -v open &> /dev/null; then
        open http://localhost:8080
    elif command -v start &> /dev/null; then
        start http://localhost:8080
    else
        print_warning "Could not detect browser command"
        echo "Please open manually: http://localhost:8080"
    fi
}

main() {
    while true; do
        show_menu
        read -p "Enter your choice (1-9): " choice
        echo ""

        case $choice in
            1)
                start_kafka
                read -p "Press Enter to continue..."
                ;;
            2)
                stop_kafka
                read -p "Press Enter to continue..."
                ;;
            3)
                show_status
                read -p "Press Enter to continue..."
                ;;
            4)
                show_kafka_logs
                ;;
            5)
                if ! check_kafka_running; then
                    read -p "Press Enter to continue..."
                    continue
                fi
                if ! check_python_dependencies; then
                    read -p "Press Enter to continue..."
                    continue
                fi
                run_connection_test
                read -p "Press Enter to continue..."
                ;;
            6)
                if ! check_kafka_running; then
                    read -p "Press Enter to continue..."
                    continue
                fi
                if ! check_python_dependencies; then
                    read -p "Press Enter to continue..."
                    continue
                fi
                run_producer
                read -p "Press Enter to continue..."
                ;;
            7)
                if ! check_kafka_running; then
                    read -p "Press Enter to continue..."
                    continue
                fi
                if ! check_python_dependencies; then
                    read -p "Press Enter to continue..."
                    continue
                fi
                run_consumer
                read -p "Press Enter to continue..."
                ;;
            8)
                open_kafka_ui
                read -p "Press Enter to continue..."
                ;;
            9)
                print_success "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please try again."
                read -p "Press Enter to continue..."
                ;;
        esac

        echo ""
    done
}

# Run main
main
