import { api } from "@/lib/api";
import KnowledgeDeepDive from "@/components/knowledge/KnowledgeDeepDive";
import { notFound } from "next/navigation";

async function getKnowledge(id: string) {
  try {
    return await api.pois.knowledge(parseInt(id, 10));
  } catch {
    return null;
  }
}

export default async function PoiKnowledgePage({ params }: { params: { id: string } }) {
  const data = await getKnowledge(params.id);
  if (!data) notFound();

  return (
    <div style={{ minHeight: "100%", background: "var(--city-surface)" }}>
      <div style={{ padding: "1rem", borderBottom: "1px solid #e5e7eb", background: "white" }}>
        <a href="/pois" style={{ color: "var(--city-accent)", fontSize: "0.875rem", fontWeight: 600, textDecoration: "none" }}>
          ← Back to Places
        </a>
      </div>
      <KnowledgeDeepDive data={data as any} />
    </div>
  );
}
