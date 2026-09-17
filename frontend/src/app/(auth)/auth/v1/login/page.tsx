import { LoginBrandPanel } from "./_components/login-brand-panel";

export default function LoginV1() {
  return (
    <div className="flex h-dvh">
      <LoginBrandPanel />

      <div className="flex w-full items-center justify-center bg-background p-8 lg:w-2/3">
        <div className="w-full max-w-md space-y-10 py-24 lg:py-32">
          <div className="space-y-4 text-center">
            <div className="font-medium tracking-tight">Login</div>
            <div className="mx-auto max-w-xl text-muted-foreground">
              Masuk dengan akun BackOne Anda untuk mengakses dashboard.
            </div>
          </div>
          {/* Server-rendered form posts form-encoded to BFF; no JS required */}
          <form
            action="/api/auth/login/"
            method="POST"
            className="flex flex-col gap-4"
          >
            <input type="hidden" name="next" value="/" />
            <div className="space-y-4">
              <label htmlFor="id_username" className="block text-sm font-medium">
                Username
              </label>
              <input
                id="id_username"
                name="username"
                type="text"
                required
                autoComplete="username"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
              <label htmlFor="id_password" className="block text-sm font-medium">
                Password
              </label>
              <input
                id="id_password"
                name="password"
                type="password"
                required
                autoComplete="current-password"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <button
              type="submit"
              className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Login
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
