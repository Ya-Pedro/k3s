# k3s

kubectl exec -it -n database crud-db-postgresql-0 -- psql -U postgres -d postgres -c "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name VARCHAR(100), surname VARCHAR(100), age INT, town VARCHAR(100));"

kubectl exec -it -n database crud-db-postgresql-0 -- psql -U postgres -d postgres -c "\dt"


 curl -X POST http://192.168.122.57:30081/users \
     -H "Content-Type: application/json" \
     -d '{"name": "Pedro", "surname": "Laba", "age": 21, "town": "Moscow"}'


curl -X GET http://192.168.122.57:30081/users/2


https://192.168.122.57:30080/ #argo
http://192.168.122.57:30082 #grafana
http://192.168.122.57:30081/status #flask