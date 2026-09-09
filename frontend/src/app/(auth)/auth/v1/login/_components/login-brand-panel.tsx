"use client";

import * as React from "react";

export function LoginBrandPanel() {
  // Random seed per client load → pulls a fresh random photo each visit.
  const [seed] = React.useState(() => Math.random().toString(36).slice(2));
  const img = `https://picsum.photos/seed/${seed}/800/1200`;

  return (
    <div
      className="hidden bg-cover bg-center lg:block lg:w-1/3"
      style={{ backgroundImage: `url("${img}")` }}
    >
      <div className="flex h-full flex-col items-center justify-center bg-black/40 p-12 text-center">
        <div className="space-y-6">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/backone-logo.svg" alt="BackOne" className="mx-auto size-16" />
          <div className="space-y-2">
            <h1 className="font-light text-5xl text-primary-foreground">BackOne Data</h1>
            <p className="text-primary-foreground/80 text-xl">Dashboard manajemen situs jaringan</p>
          </div>
        </div>
      </div>
    </div>
  );
}
