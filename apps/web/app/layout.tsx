import type { ReactNode } from "react";

// Root layout used by every page in the app.
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
