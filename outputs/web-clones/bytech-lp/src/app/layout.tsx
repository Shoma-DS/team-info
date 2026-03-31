import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Bytech | AIスキル習得スクール",
  description:
    "Bytechは現役プロ講師による実践型AIスキルスクール。ChatGPT・Copilot・Difyなど全10コース600レッスンで、副業・転職・業務改善に直結するAIスキルを習得できます。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className="h-full antialiased">
      <head>
        {/* Noto Sans JP — primary font (Google Fonts CDN, loaded at runtime) */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
