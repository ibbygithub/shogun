"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import SakuraStatus from "@/components/ambient/SakuraStatus";

interface SakuraResult {
  title: string;
  url: string;
  summary: string;
  score: number;
}

interface SakuraData {
  city: string;
  results: SakuraResult[];
  query_time: string;
  error?: string;
}

interface Props {
  slug: string;
}

export default function CityBlossomSection({ slug }: Props) {
  const [data, setData] = useState<SakuraData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.ambient.sakura(slug)
      .then((d) => setData(d as SakuraData))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [slug]);

  return <SakuraStatus data={data} loading={loading} />;
}
