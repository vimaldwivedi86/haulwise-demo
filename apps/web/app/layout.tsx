import type { Metadata } from "next";
import Link from "next/link";
import "leaflet/dist/leaflet.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Haulwise",
  description: "Demo fleet platform",
};

const NAV = [
  { href: "/", label: "Live Map" },
  { href: "/video", label: "Video Safety" },
  { href: "/driver", label: "Driver App" },
  { href: "/vendor", label: "Vendor Traffic" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="topbar">
            <span className="brand">Haulwise</span>
            <nav>
              {NAV.map((item) => (
                <Link key={item.href} href={item.href}>
                  {item.label}
                </Link>
              ))}
            </nav>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  );
}
