# Demonstração da Ferramenta

## Objetivo
Demonstrar a execução da ferramenta de simulação IoHT-FL com cinco cenários:

| # | Cenário | Agregador | Consenso | Propósito |
|---|---------|-----------|----------|-----------|
| 1 | Baseline | FedAvg | Threshold | IID, sem falhas (referência) |
| 2 | Non-IID | Weighted | Voting | Dados não-IID com votação |
| 3 | Robusto | Robust | Threshold | Falhas intra-rodada |
| 4 | MultiKrum | MultiKrum | Threshold | Tolerância a Bizantinos |
| 5 | HotStuff | FedAvg | HotStuff | Consenso BFT via comitê |

## Passos
```bash
python scripts/run_demo.py --config config/scenario_baseline.json
python scripts/run_demo.py --config config/scenario_non_iid.json
python scripts/run_demo.py --config config/scenario_robust.json
python scripts/run_demo.py --config config/scenario_multi_krum.json
python scripts/run_demo.py --config config/scenario_hotstuff.json
```

## Resultados esperados
- Geração de arquivos CSV e JSON em `results/` para cada cenário.
- Registro por rodada de participação, custo de comunicação e proxy de acurácia.
- Comparação entre agregadores (FedAvg, Weighted, Robust, MultiKrum) e consensos (Threshold, Voting, HotStuff).
- Logs com contexto estruturado (rodada, método, cliente).

## Caso de uso simples
A ferramenta simula dispositivos IoHT distribuídos entre ambientes residencial, clínico e hospitalar. Cada cliente treina localmente com dados sintéticos de sinais vitais e envia atualizações para o servidor FL, que aplica consenso e agregação para atualizar o modelo global.

## Execução individual
Para executar um cenário específico com parâmetros customizados:
```bash
python scripts/run_demo.py --config config/scenario_baseline.json \
    --log-level INFO --log-format json
```
