from app.api.routes import chat as chat_module
from app.schemas.epidemiology import ChatSource


def test_document_snippets_deprioritizes_pandemic_by_default():
    # Prepare fake DB sources: one recent (2023), two pandemic-era (2020, 2021)
    recent = ChatSource(title="reciente", excerpt="datos actuales 2023", source_type="doc", publication_date="2023-06-01")
    pandemic1 = ChatSource(title="pandemia-2020", excerpt="informe 2020 covid impacto", source_type="doc", publication_date="2020-05-01")
    pandemic2 = ChatSource(title="pandemia-2021", excerpt="reporte 2021 covid y brotes", source_type="doc", publication_date="2021-07-01")

    # Monkeypatch the DB search function in the chat module
    def fake_search(q, limit=3):
        return [pandemic1, pandemic2, recent]

    chat_module._search_knowledge_base = fake_search

    snippets = chat_module._document_snippets("¿Cuál es la situación actual?", limit=3)
    assert len(snippets) == 3
    # Expect recent first (not pandemic) because question doesn't mention 2020/2021/covid
    assert snippets[0].title == "reciente"


def test_document_snippets_includes_pandemic_when_asked():
    recent = ChatSource(title="reciente", excerpt="datos actuales 2023", source_type="doc", publication_date="2023-06-01")
    pandemic = ChatSource(title="pandemia-2020", excerpt="informe 2020 covid impacto", source_type="doc", publication_date="2020-05-01")

    def fake_search(q, limit=3):
        return [recent, pandemic]

    chat_module._search_knowledge_base = fake_search

    snippets = chat_module._document_snippets("Mostrar datos de 2020 sobre dengue", limit=2)
    assert len(snippets) == 2
    # Because the question mentions 2020, pandemic doc should be present (order can include it)
    titles = [s.title for s in snippets]
    assert "pandemia-2020" in titles
