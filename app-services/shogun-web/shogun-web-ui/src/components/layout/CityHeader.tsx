"use client";

import { useEffect } from "react";
import type { CitySlug } from "@/lib/cities";
import { CITIES } from "@/lib/cities";

interface CityHeaderProps {
  slug: CitySlug;
}

export default function CityHeader({ slug }: CityHeaderProps) {
  const city = CITIES[slug];

  // Apply data-city attribute to html root so CSS vars take effect
  useEffect(() => {
    document.documentElement.setAttribute("data-city", slug);
    return () => document.documentElement.removeAttribute("data-city");
  }, [slug]);

  return null; // purely a side-effect component
}
