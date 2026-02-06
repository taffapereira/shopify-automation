"""
📊 Dashboard de Monitoramento
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List


class Dashboard:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.metricas_file = self.data_dir / "metricas.json"

    def registrar_mineracao(self, minerados: int, aprovados: int, score_medio: float = 0):
        hoje = datetime.now().strftime("%Y-%m-%d")
        metricas = self._carregar_metricas()

        if hoje not in metricas:
            metricas[hoje] = {"minerados": 0, "aprovados": 0, "sincronizados": 0, "score_total": 0, "count": 0}

        metricas[hoje]["minerados"] += minerados
        metricas[hoje]["aprovados"] += aprovados
        metricas[hoje]["score_total"] += score_medio * aprovados
        metricas[hoje]["count"] += aprovados

        self._salvar_metricas(metricas)

    def registrar_sincronizacao(self, quantidade: int):
        hoje = datetime.now().strftime("%Y-%m-%d")
        metricas = self._carregar_metricas()
        if hoje not in metricas:
            metricas[hoje] = {"minerados": 0, "aprovados": 0, "sincronizados": 0, "score_total": 0, "count": 0}
        metricas[hoje]["sincronizados"] += quantidade
        self._salvar_metricas(metricas)

    def _carregar_metricas(self) -> Dict:
        if self.metricas_file.exists():
            with open(self.metricas_file, 'r') as f:
                return json.load(f)
        return {}

    def _salvar_metricas(self, metricas: Dict):
        with open(self.metricas_file, 'w') as f:
            json.dump(metricas, f, indent=2)

    def obter_resumo_hoje(self) -> Dict:
        hoje = datetime.now().strftime("%Y-%m-%d")
        metricas = self._carregar_metricas()

        if hoje in metricas:
            m = metricas[hoje]
            taxa = (m["aprovados"] / m["minerados"] * 100) if m["minerados"] > 0 else 0
            score = (m["score_total"] / m["count"]) if m["count"] > 0 else 0
            return {"data": hoje, "minerados": m["minerados"], "aprovados": m["aprovados"],
                    "taxa": round(taxa, 1), "sincronizados": m["sincronizados"], "score": round(score, 1)}
        return {"data": hoje, "minerados": 0, "aprovados": 0, "taxa": 0, "sincronizados": 0, "score": 0}

    def obter_resumo_semana(self) -> List[Dict]:
        metricas = self._carregar_metricas()
        resumo = []
        for i in range(7):
            data = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if data in metricas:
                m = metricas[data]
                taxa = (m["aprovados"] / m["minerados"] * 100) if m["minerados"] > 0 else 0
                score = (m["score_total"] / m["count"]) if m["count"] > 0 else 0
                resumo.append({"data": data, "minerados": m["minerados"], "aprovados": m["aprovados"],
                               "taxa": round(taxa, 1), "sincronizados": m["sincronizados"], "score": round(score, 1)})
            else:
                resumo.append({"data": data, "minerados": 0, "aprovados": 0, "taxa": 0, "sincronizados": 0, "score": 0})
        return resumo

    def imprimir_dashboard(self):
        hoje = self.obter_resumo_hoje()
        semana = self.obter_resumo_semana()

        print("\n" + "="*60)
        print("📊 DASHBOARD - TWP Acessórios")
        print("="*60)
        print(f"\n📅 HOJE ({hoje['data']}):")
        print(f"   📦 Minerados: {hoje['minerados']}")
        print(f"   ✅ Aprovados: {hoje['aprovados']}")
        print(f"   📈 Taxa: {hoje['taxa']}%")
        print(f"   🔄 Sincronizados: {hoje['sincronizados']}")
        print(f"   ⭐ Score: {hoje['score']}")

        print(f"\n📊 ÚLTIMOS 7 DIAS:")
        print("-"*60)
        for d in semana:
            print(f"{d['data']} | Min:{d['minerados']:>3} | Apr:{d['aprovados']:>3} | Taxa:{d['taxa']:>5.1f}% | Sync:{d['sincronizados']:>3}")
        print("="*60)


if __name__ == "__main__":
    Dashboard().imprimir_dashboard()

