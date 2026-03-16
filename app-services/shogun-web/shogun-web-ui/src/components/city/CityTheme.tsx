"use client";

import { useEffect } from "react";
import type { CitySlug } from "@/lib/cities";

export default function CityTheme({ slug }: { slug: CitySlug }) {
  useEffect(() => {
    document.documentElement.setAttribute("data-city", slug);
    return () => document.documentElement.removeAttribute("data-city");
  }, [slug]);

  return null;
}
