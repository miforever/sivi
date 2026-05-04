"use client";

import ScrollReveal from "./ScrollReveal";

const plans = [
  {
    name: "Free",
    price: "0",
    period: "",
    description: "Get started with the basics",
    features: [
      "1 AI-generated resume",
      "Upload existing CV",
      "Basic job matching",
      "Community support",
    ],
    cta: "Start Free",
    href: "https://t.me/SiviAIBot",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "3",
    period: "/month",
    description: "For serious job seekers",
    features: [
      "Unlimited AI resumes",
      "Priority job matching",
      "Interview practice & scoring",
      "Resume enhancement",
      "Multi-language support",
      "Priority support",
    ],
    cta: "Go Pro",
    href: "https://t.me/SiviAIBot",
    highlighted: true,
  },
  {
    name: "Pay Per Use",
    price: "1",
    period: "/resume",
    description: "Pay only for what you need",
    features: [
      "Single AI resume generation",
      "Upload & enhance CV",
      "Job matching included",
      "PDF export",
    ],
    cta: "Try It",
    href: "https://t.me/SiviAIBot",
    highlighted: false,
  },
];

export default function Pricing() {
  return (
    <section id="pricing" className="relative py-28 overflow-hidden">
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-brand-500/5 blur-[150px]" />

      <div className="relative z-10 max-w-6xl mx-auto px-6">
        <ScrollReveal>
          <div className="text-center mb-16">
            <p className="text-sm uppercase tracking-[0.2em] text-brand-400 font-medium mb-3">
              Pricing
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold text-white">
              Simple, <span className="gradient-text">transparent</span> pricing
            </h2>
            <p className="text-white/50 mt-4 max-w-lg mx-auto">
              Start free. Upgrade when you&apos;re ready.
            </p>
          </div>
        </ScrollReveal>

        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {plans.map((plan, i) => (
            <ScrollReveal key={plan.name} delay={i * 0.12}>
              <div
                className={`relative h-full p-8 rounded-2xl transition-all duration-500 ${
                  plan.highlighted
                    ? "glass border-brand-500/30 hover:border-brand-500/50 shadow-[0_0_40px_rgba(236,72,153,0.1)]"
                    : "glass-light hover:bg-white/[0.08]"
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-brand-400 to-brand-500 text-xs font-semibold text-white">
                    Most Popular
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-white mb-1">
                    {plan.name}
                  </h3>
                  <p className="text-white/40 text-sm">{plan.description}</p>
                </div>

                <div className="mb-8">
                  <span className="text-4xl font-bold text-white">${plan.price}</span>
                  <span className="text-white/40 text-sm">{plan.period}</span>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-3 text-sm">
                      <svg
                        className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                          plan.highlighted ? "text-brand-400" : "text-white/30"
                        }`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                      </svg>
                      <span className="text-white/60">{feature}</span>
                    </li>
                  ))}
                </ul>

                <a
                  href={plan.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`block w-full py-3 rounded-xl text-center text-sm font-semibold transition-all duration-300 ${
                    plan.highlighted
                      ? "bg-gradient-to-r from-brand-400 to-brand-500 text-white hover:shadow-[0_0_24px_rgba(236,72,153,0.4)] hover:scale-[1.02]"
                      : "border border-white/15 text-white/80 hover:border-white/30 hover:text-white hover:bg-white/5"
                  }`}
                >
                  {plan.cta}
                </a>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
