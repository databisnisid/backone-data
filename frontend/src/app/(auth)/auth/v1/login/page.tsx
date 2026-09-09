import { Suspense } from "react";

import { LoginBrandPanel } from "./_components/login-brand-panel";


import { LoginForm } from "../../_components/login-form";

export default function LoginV1() {
  return (
    <div className="flex h-dvh">
      <LoginBrandPanel />

      <div className="flex w-full items-center justify-center bg-background p-8 lg:w-2/3">
        <Suspense fallback={<div className="h-[360px]" />}>
          <div className="w-full max-w-md space-y-10 py-24 lg:py-32">
            <div className="space-y-4 text-center">
              <div className="font-medium tracking-tight">Login</div>
              <div className="mx-auto max-w-xl text-muted-foreground">
                Masuk dengan akun BackOne Anda untuk mengakses dashboard.
              </div>
            </div>
            <LoginForm />
          </div>
        </Suspense>
      </div>
    </div>
  );
}