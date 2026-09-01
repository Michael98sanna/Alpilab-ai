import styles from "./MainSectionNav.module.css";

export type AppSection = "chat" | "diagnostics" | "programs";

interface MainSectionNavProps {
  active: AppSection;
  onChange: (section: AppSection) => void;
}

const SECTIONS: { id: AppSection; label: string; icon: string }[] = [
  { id: "chat", label: "Chat", icon: "💬" },
  { id: "diagnostics", label: "Diagnosi", icon: "🔬" },
  { id: "programs", label: "Programmi", icon: "💻" },
];

export function MainSectionNav({ active, onChange }: MainSectionNavProps) {
  return (
    <nav className={styles.nav} aria-label="Sezioni principali" data-testid="main-section-nav">
      <div className={styles.tabs}>
        {SECTIONS.map((section) => (
          <button
            key={section.id}
            type="button"
            className={`${styles.tab} ${active === section.id ? styles.active : ""}`}
            aria-current={active === section.id ? "page" : undefined}
            aria-label={section.label}
            data-testid={`section-${section.id}`}
            onClick={() => onChange(section.id)}
          >
            <span className={styles.icon} aria-hidden>
              {section.icon}
            </span>
            <span>{section.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}
