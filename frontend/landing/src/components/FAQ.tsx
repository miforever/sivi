"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useLanguage } from "@/i18n/LanguageContext";

export default function FAQ() {
  const { t } = useLanguage();
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section className="py-16 max-w-3xl mx-auto px-6">
      <h2 className="text-xl font-semibold text-fg mb-6 text-center">
        {t.faq.title}
      </h2>
      <div className="divide-y divide-fg/10 border-y border-fg/10">
        {t.faq.items.map((item, i) => (
          <div key={i}>
            <button
              onClick={() => setOpen(open === i ? null : i)}
              className="w-full flex items-center justify-between gap-4 py-3.5 text-left text-sm font-medium text-fg hover:text-fg/80 transition-colors"
            >
              <span>{item.q}</span>
              <span className="flex-shrink-0 text-fg/40 text-base leading-none">
                {open === i ? "−" : "+"}
              </span>
            </button>
            <AnimatePresence initial={false}>
              {open === i && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2, ease: "easeInOut" }}
                  className="overflow-hidden"
                >
                  <p className="pb-4 text-sm text-fg/55 leading-relaxed">
                    {item.a}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </section>
  );
}
