"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import { useLanguage } from "@/i18n/LanguageContext";
import { useTheme } from "@/i18n/ThemeContext";
import type { Locale } from "@/i18n/translations";

const localeLabels: Record<Locale, string> = {
  uz: "UZ",
  ru: "RU",
  en: "EN",
};

function SunIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1.5M12 19.5V21M4.22 4.22l1.06 1.06M18.72 18.72l1.06 1.06M3 12h1.5M19.5 12H21M4.22 19.78l1.06-1.06M18.72 5.28l1.06-1.06M16.5 12a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0z" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.72 9.72 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
    </svg>
  );
}

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);
  const langRef = useRef<HTMLDivElement>(null);
  const { locale, setLocale, t } = useLanguage();
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (langRef.current && !langRef.current.contains(e.target as Node)) {
        setLangOpen(false);
      }
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  const navLinks = [
    { href: "#features", label: t.nav.features },
    { href: "#how-it-works", label: t.nav.howItWorks },
    { href: "#about", label: t.nav.about },
  ];

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 flex justify-center"
    >
      <motion.div
        className="relative"
        animate={{ marginTop: scrolled ? 12 : 0 }}
        transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
      >
        {/* Background pill — animates from full-width to content-width */}
        <motion.div
          className="absolute top-0 bottom-0 glass"
          animate={{
            left: scrolled ? 0 : -2000,
            right: scrolled ? 0 : -2000,
            borderRadius: scrolled ? 9999 : 0,
          }}
          transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
        />

        {/* Content — stays in place */}
        <motion.div
          className="relative z-10 flex items-center"
          animate={{
            paddingTop: scrolled ? 12 : 20,
            paddingBottom: scrolled ? 12 : 20,
          }}
          transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
          style={{ paddingLeft: 40, paddingRight: 40 }}
        >
          {/* Logo — left */}
          <a href="#" className="flex items-center gap-2.5 group">
            <Image
              src="/logo.png"
              alt="Sivi"
              width={36}
              height={36}
              className="group-hover:scale-110 transition-transform duration-300"
            />
            <span className="text-xl font-bold tracking-tight text-fg">
              Sivi
            </span>
          </a>

          {/* Desktop nav — center */}
          <div className="hidden md:flex items-center gap-8 mx-12">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-sm text-fg/70 hover:text-fg transition-colors duration-200 relative group"
              >
                {link.label}
                <span className="absolute -bottom-1 left-0 w-0 h-px bg-brand-400 group-hover:w-full transition-all duration-300" />
              </a>
            ))}
          </div>

          {/* CTA + Language + Theme — right */}
          <div className="hidden md:flex items-center gap-3">
            <a
              href="https://t.me/SiviAIBot"
              target="_blank"
              rel="noopener noreferrer"
              className="px-5 py-2 rounded-full text-sm font-semibold text-white bg-gradient-to-r from-brand-400 to-brand-500 hover:from-brand-500 hover:to-brand-600 transition-all duration-300 hover:shadow-[0_0_24px_rgba(236,72,153,0.4)]"
            >
              {t.nav.tryFree}
            </a>

            {/* Language dropdown */}
            <div ref={langRef} className="relative">
              <button
                onClick={() => setLangOpen(!langOpen)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-fg/60 hover:text-fg border border-fg/10 hover:border-fg/25 transition-all duration-200"
              >
                {localeLabels[locale]}
                <svg
                  className={`w-3 h-3 transition-transform duration-200 ${langOpen ? "rotate-180" : ""}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
              </button>

              <AnimatePresence>
                {langOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 mt-2 py-1 rounded-xl glass overflow-hidden min-w-[72px]"
                  >
                    {(Object.keys(localeLabels) as Locale[]).map((l) => (
                      <button
                        key={l}
                        onClick={() => {
                          setLocale(l);
                          setLangOpen(false);
                        }}
                        className={`w-full px-4 py-1.5 text-xs text-left transition-colors ${
                          l === locale
                            ? "text-brand-500 bg-fg/5"
                            : "text-fg/50 hover:text-fg hover:bg-fg/5"
                        }`}
                      >
                        {localeLabels[l]}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Theme toggle — right of language switch */}
            <button
              onClick={toggleTheme}
              aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              className="flex items-center justify-center w-8 h-8 rounded-full text-fg/60 hover:text-fg border border-fg/10 hover:border-fg/25 transition-all duration-200"
            >
              {theme === "dark" ? <SunIcon /> : <MoonIcon />}
            </button>
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden ml-8 relative w-8 h-8 flex flex-col items-center justify-center gap-1.5"
            aria-label="Toggle menu"
          >
            <span
              className={`w-5 h-0.5 bg-fg transition-all duration-300 ${
                mobileOpen ? "rotate-45 translate-y-1" : ""
              }`}
            />
            <span
              className={`w-5 h-0.5 bg-fg transition-all duration-300 ${
                mobileOpen ? "-rotate-45 -translate-y-1" : ""
              }`}
            />
          </button>
        </motion.div>
      </motion.div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="absolute top-full md:hidden glass mt-2 mx-4 rounded-2xl overflow-hidden w-[calc(100%-2rem)]"
          >
            <div className="p-6 flex flex-col gap-4">
              {navLinks.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="text-fg/80 hover:text-fg transition-colors py-1"
                >
                  {link.label}
                </a>
              ))}

              {/* Mobile language selector + theme toggle */}
              <div className="flex items-center justify-between gap-2 pt-2 border-t border-fg/10">
                <div className="flex gap-2">
                  {(Object.keys(localeLabels) as Locale[]).map((l) => (
                    <button
                      key={l}
                      onClick={() => {
                        setLocale(l);
                        setMobileOpen(false);
                      }}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                        l === locale
                          ? "bg-brand-500/20 text-brand-500 border border-brand-500/30"
                          : "text-fg/40 border border-fg/10 hover:text-fg/70"
                      }`}
                    >
                      {localeLabels[l]}
                    </button>
                  ))}
                </div>
                <button
                  onClick={toggleTheme}
                  aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
                  className="flex items-center justify-center w-9 h-9 rounded-full text-fg/60 hover:text-fg border border-fg/10 hover:border-fg/25 transition-all duration-200"
                >
                  {theme === "dark" ? <SunIcon /> : <MoonIcon />}
                </button>
              </div>

              <a
                href="https://t.me/SiviAIBot"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 px-5 py-2.5 rounded-full text-center font-semibold text-white bg-gradient-to-r from-brand-400 to-brand-500"
              >
                {t.nav.tryFree}
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}
