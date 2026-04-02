# RELATÓRIO FINAL DE REVISÃO E PLANEJAMENTO — SIGDT (V4.0)

## 1. DIAGNÓSTICO CONSOLIDADO

Após a análise cruzada de múltiplos relatórios técnicos, confirma-se que o projeto SIGDT possui uma base funcional sólida e um modelo relacional bem estruturado (V4), porém apresenta falhas críticas de segurança, arquitetura e performance que impedem seu uso seguro em produção. 

Os pontos de concordância absoluta entre as revisões sinalizam a necessidade imediata de uma intervenção em três frentes: **Segurança Operacional**, **Integridade de Dados/Deploy** e **Refatoração Estrutural**.

---

## 2. PONTOS CRÍTICOS DE CONCORDÂNCIA (Ação Necessária)

### 🛡️ Segurança Operacional
1.  **Ausência de Proteção CSRF:** O sistema está vulnerável a ataques de Cross-Site Request Forgery em todas as rotas de alteração de dados (`POST`, `DELETE`).
2.  **Gestão de Segredos Insegura:** Uso de fallbacks previsíveis para `SECRET_KEY` e exposição de credenciais reais (`ADMIN_PASSWORD`, `GATEKEEPER_PASSWORD`) em arquivos versionados ou documentação.
3.  **Uploads e Anexos Expostos:** PDFs técnicos são servidos via diretório `static` público, sem controle de autorização para o download.

### 🏗️ Arquitetura e Integridade
4.  **Divergência Modelos vs. Migrações:** O esquema atual do banco (especialmente chaves primárias string) não está perfeitamente alinhado com a cadeia de migrações do Alembic.
5.  **Conflito no Startup do Banco:** Uso simultâneo de `SQLModel.metadata.create_all()` e Alembic, o que mascara falhas de migração e gera "schema drift".
6.  **God Module (`main.py`):** Concentração excessiva de lógica em um único arquivo (600+ linhas), dificultando manutenção e testes.

### ⚙️ Performance e Confiabilidade
7.  **Processamento de CSV Ineficiente:** Carga integral de arquivos na memória e múltiplas queries individuais por linha (problema de N+1 e OOM).
8.  **Baixa Cobertura de Testes:** Testes insuficientes, dependentes de estado global e sem cobertura de cenários negativos ou fluxos críticos (Upload/Snapshot).

---

## 3. PLANO DE IMPLEMENTAÇÃO (ROADMAP)

### FASE 1: Estabilização e Segurança Crítica (Prioridade Máxima)
*Objetivo: Fechar brechas de segurança e proteger segredos.*

1.  **Sanitização de Segredos:**
    *   Rotacionar todas as senhas e `SECRET_KEY`.
    *   Expurgar o arquivo `.env` do histórico do Git (usando BFG ou filter-branch).
    *   Implementar falha no startup se variáveis obrigatórias estiverem ausentes (remover fallbacks).
2.  **Proteção Anti-CSRF:**
    *   Implementar middleware de proteção global.
    *   Integrar tokens CSRF em todos os formulários e headers do HTMX.
3.  **Correção de Bootstrap:**
    *   Tornar a criação do usuário `admin` idempotente, removendo o reset forçado de senha a cada boot.
4.  **Proteção de Anexos:**
    *   Mover uploads para fora da pasta `static`.
    *   Criar rota autenticada para servir arquivos PDF.

### FASE 2: Integridade Arquitetural e Refatoração
*Objetivo: Modularizar o sistema e consolidar o fluxo de dados.*

1.  **Reconciliação de Banco de Dados:**
    *   Consolidar todas as migrations para refletir o schema V4 real.
    *   Remover `create_all()` do fluxo de execução normal (manter apenas para testes).
2.  **Modularização do `main.py`:**
    *   Extrair rotas para sub-módulos (`routers/`).
    *   Isolar lógica de permissão e helpers de segurança.
3.  **Consolidação de Frontend:**
    *   Implementar `base.html` com herança Jinja2 para eliminar duplicação de Navbar e Scripts.
    *   Internalizar dependências (Tailwind/HTMX) para evitar dependência de CDNs externas em ambiente militar restrito.

### FASE 3: Performance e Validação
*Objetivo: Otimizar o processamento e garantir regressão zero.*

1.  **Otimização do CSV Service:**
    *   Implementar processamento em chunks (lotes) para reduzir consumo de memória.
    *   Usar cache de lookup pré-carregado para evitar N+1 queries durante a importação.
2.  **Eager Loading no Dashboard:**
    *   Ajustar queries principais para usar `selectinload`, eliminando o problema de N+1 na listagem.
3.  **Suíte de Testes Robusta:**
    *   Implementar isolamento de banco de dados por teste (fixtures efêmeras).
    *   Adicionar testes de integração para o fluxo de Snapshot e deduplicação de CSV.

---

## 4. TOP 5 AÇÕES IMEDIATAS

| Ordem | Ação | Impacto |
| :--- | :--- | :--- |
| **1** | Remover fallback de `SECRET_KEY` e falhar se ausente. | Segurança |
| **2** | Implementar Middleware CSRF e tokens em formulários. | Segurança |
| **3** | Alinhar Migrations Alembic com schema V4 real. | Integridade |
| **4** | Criar `base.html` e unificar Navbar/Logout. | Manutenção |
| **5** | Mover anexos PDF para rota autenticada. | Segurança |

---
**Status:** Planejamento Finalizado. Pronto para execução da Fase 1.
