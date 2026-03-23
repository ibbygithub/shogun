import { api } from "@/lib/api";
import PoiGuideView from "@/components/pois/PoiGuideView";
import KnowledgeDeepDive from "@/components/knowledge/KnowledgeDeepDive";
import { notFound } from "next/navigation";
import type { PoiGuideResponse } from "@/lib/types";

async function getGuide(id: string) {
  try {
    return await api.pois.guide(parseInt(id, 10)) as PoiGuideResponse;
  } catch {
    return null;
  }
}

async function getKnowledge(id: string) {
  try {
    return await api.pois.knowledge(parseInt(id, 10));
  } catch {
    return null;
  }
}

export default async function PoiDetailPage({ params }: { params: { id: string } }) {
  const guideData = await getGuide(params.id);

  // If guide endpoint returned data with a guide, show the rich view
  if (guideData?.has_guide && guideData.guide) {
    return (
      <div style={{ minHeight: "100%", background: "var(--city-surface, #f9fafb)" }}>
        <div style={{ padding: "1rem", borderBottom: "1px solid #e5e7eb", background: "white" }}>
          <a href="/pois" style={{ color: "var(--city-accent)", fontSize: "0.875rem", fontWeight: 600, textDecoration: "none" }}>
            &larr; Back to Places
          </a>
        </div>
        <PoiGuideView poi={guideData.poi} guide={guideData.guide} />
      </div>
    );
  }

  // Fall back to the old knowledge view
  const knowledgeData = await getKnowledge(params.id);
  if (!knowledgeData) notFound();

  return (
    <div style={{ minHeight: "100%", background: "var(--city-surface)" }}>
      <div style={{ padding: "1rem", borderBottom: "1px solid #e5e7eb", background: "white" }}>
        <a href="/pois" style={{ color: "var(--city-accent)", fontSize: "0.875rem", fontWeight: 600, textDecoration: "none" }}>
          &larr; Back to Places
        </a>
      </div>
      <KnowledgeDeepDive data={knowledgeData as any} />
    </div>
  );
}
