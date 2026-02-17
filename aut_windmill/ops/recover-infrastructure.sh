#!/bin/bash
# ???? RECUPERAR SISTEMA BASE - Herramienta de desarrollo principal

echo "???? RECUPERANDO TU SISTEMA BASE DE DESARROLLO..."
echo ""

# Detener contenedores de Cyn temporalmente
echo "??????  Deteniendo contenedores de Cyn temporalmente..."
docker-compose -f docker-compose-cyn.yml stop

# Iniciar sistema base
echo "???? Iniciando sistema base de desarrollo..."
docker-compose -f docker-compose-infraestructure.yml up -d windmill-dev postgres-dev redis-dev

echo ""
echo "??? SISTEMA BASE RECUPERADO:"
echo "   ???? Windmill Dev: http://localhost:8000"
echo "   ???????  PostgreSQL Dev: Puerto 5432"
echo "   ???? Redis Dev: Puerto 6379"
echo ""
echo "??? SISTEMA DE CYN TAMBI??N DISPONIBLE:"
echo "   ???? Windmill Cyn: http://localhost:8001"
echo "   ???????  PostgreSQL Cyn: Puerto 5433"
echo "   ???? Redis Cyn: Puerto 6380"
echo ""
echo "???? ARQUITECTURA CORRECTA:"
echo "   ???? Puerto 8000 ??? TU HERRAMIENTA DE DESARROLLO"
echo "   ???? Puerto 8001 ??? CLIENTE CYN (Einstein Kids)"
echo "   ???? Puerto 8002 ??? CLIENTE 2 (Pr??ximo cliente)"
echo "   ???? Puerto 8003 ??? CLIENTE 3 (Futuro cliente)"
echo ""
echo "???? BENEFICIOS DE ESTA ARQUITECTURA:"
echo "   ??? T?? trabajas en localhost:8000 (tu sistema)"
echo "   ??? Cyn accede a localhost:8001 (solo su info)"
echo "   ??? Cada cliente tiene su puerto aislado"
echo "   ??? Puedes escalar infinitamente (8002, 8003, etc.)"
echo "   ??? Cada cliente paga por su instancia aislada"
echo ""
echo "??????  CREDENCIALES DE ACCESO:"
echo "   ???? Sistema Base (8000): admin@tu-empresa.com / TuPassword"
echo "   ???? Cyn (8001): <CLIENT_ADMIN_EMAIL> / <CLIENT_ADMIN_PASSWORD>"
echo ""
echo "???? ??YA PUEDES AUTOMATIZAR TODA TU INFRAESTRUCTURA!"
echo "   ??? Cliente nuevo? Agregar puerto 8002, 8003, etc."
echo "   ??? Cada cliente ve solo SU sistema"
echo "   ??? T?? controlas TODO desde tu sistema base"
