"""
Locustfile para testes de carga da API de Recomendações Educacionais.

ENDPOINTS CORRETOS:
- GET /api/v1/recommendations/{user_id}
- POST /api/v1/recommendations/feedback

Certifique-se de que está usando este arquivo atualizado!
"""
import os
import random
from locust import HttpUser, task, between

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"

# Usuários de teste (serão criados automaticamente se não existirem)
BASE_USERS = [1, 2, 3, 4, 5]

# Verificação: se você vê endpoints /recommend ou /feedback nos logs,
# está usando uma versão antiga deste arquivo!

class ApiUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Executado quando um usuário virtual inicia"""
        self.user_id_index = random.choice(BASE_USERS)
        self.token, self.user_id = self.get_auth_token_and_user_id()
        if self.token:
            self.client.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
    
    def get_auth_token_and_user_id(self):
        """Obtém token de autenticação e ID real do usuário, criando usuário se necessário"""
        username = f"locust_user_{self.user_id_index}"
        password = "test_password"
        
        # Tenta fazer login
        login_response = self.client.post(
            f"{API_PREFIX}/auth/login",
            data={"username": username, "password": password},
            name="POST /auth/login",
            catch_response=True
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            # Obter ID real do usuário via /auth/me
            user_id = self.get_user_id(token)
            if user_id:
                return token, user_id
        
        # Se login falhar, tenta registrar
        register_response = self.client.post(
            f"{API_PREFIX}/auth/register",
            json={
                "username": username,
                "email": f"{username}@example.com",
                "password": password
            },
            name="POST /auth/register",
            catch_response=True
        )
        
        if register_response.status_code in [201, 400]:
            # Se registro foi bem-sucedido, pode obter ID da resposta
            user_id = None
            if register_response.status_code == 201:
                try:
                    user_id = register_response.json().get("id")
                except:
                    pass
            
            # Após registro, tenta login novamente
            login_response2 = self.client.post(
                f"{API_PREFIX}/auth/login",
                data={"username": username, "password": password},
                name="POST /auth/login",
                catch_response=True
            )
            if login_response2.status_code == 200:
                token = login_response2.json().get("access_token")
                # Se não obteve ID do registro, obtém via /auth/me
                if not user_id:
                    user_id = self.get_user_id(token)
                return token, user_id
        
        return None, None
    
    def get_user_id(self, token):
        """Obtém o ID real do usuário autenticado"""
        try:
            # Fazer requisição com headers temporários
            me_response = self.client.get(
                f"{API_PREFIX}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                name="GET /auth/me",
                catch_response=True
            )
            if me_response.status_code == 200:
                return me_response.json().get("id")
        except:
            pass
        
        return None

    @task(4)  # read-heavy
    def get_recommendation(self):
        """GET /recommendations/{user_id}"""
        if not self.token or not self.user_id:
            return
        
        with self.client.get(
            f"{API_PREFIX}/recommendations/{self.user_id}",
            name="GET /recommendations/{user_id}",
            catch_response=True
        ) as res:
            if res.status_code == 200:
                res.success()
            else:
                res.failure(f"status: {res.status_code}")

    @task(3)  # write
    def post_feedback(self):
        """POST /recommendations/feedback"""
        if not self.token or not self.user_id:
            return
        
        payload = {
            "user_id": self.user_id,
            "content_id": f"content_basico_{self.user_id}_{random.randint(1000, 9999)}",
            "reward": random.uniform(0.3, 0.9),
            "interaction_type": random.choice(["view", "complete", "skip"])
        }
        
        with self.client.post(
            f"{API_PREFIX}/recommendations/feedback",
            json=payload,
            name="POST /recommendations/feedback",
            catch_response=True
        ) as res:
            if res.status_code in (200, 201):
                res.success()
            else:
                res.failure(f"status: {res.status_code}")