#!/bin/bash

# Stop all Rafiki AI Docker services

echo "🛑 Stopping Rafiki AI..."

docker-compose down

echo "✅ All services stopped"
echo ""
echo "💡 To remove all data:"
echo "   docker-compose down -v"
echo ""
echo "💡 To remove images:"
echo "   docker system prune -a"
