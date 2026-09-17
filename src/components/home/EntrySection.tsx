'use client';

import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';

export interface EntryItem {
    title: string;
    date?: string;
    url?: string;
    description?: string;
}

interface EntrySectionProps {
    title?: string;
    intro?: string;
    entries: EntryItem[];
}

export default function EntrySection({ title, intro, entries }: EntrySectionProps) {
    return (
        <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
        >
            {title && (
                <h2 className="text-2xl font-serif font-bold text-primary mb-4">{title}</h2>
            )}
            {intro && (
                <p className="text-neutral-700 dark:text-neutral-600 leading-relaxed mb-5">{intro}</p>
            )}
            <div className="space-y-5">
                {entries.map((entry, index) => {
                    const isExternal = /^https?:\/\//i.test(entry.url || '');
                    return (
                        <article key={`${entry.title}-${index}`}>
                            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-2">
                                <h3 className="text-lg font-serif font-semibold text-primary">
                                    {entry.url ? (
                                        <a
                                            href={entry.url}
                                            target={isExternal ? '_blank' : undefined}
                                            rel={isExternal ? 'noopener noreferrer' : undefined}
                                            className="text-accent transition-all duration-200 rounded hover:bg-accent/10 hover:shadow-sm"
                                        >
                                            {entry.title}
                                        </a>
                                    ) : entry.title}
                                </h3>
                                {entry.date && (
                                    <time className="text-xs text-neutral-500 dark:text-neutral-500 tabular-nums">
                                        {entry.date}
                                    </time>
                                )}
                            </div>
                            {entry.description && (
                                <div className="text-sm text-neutral-700 dark:text-neutral-600 leading-6">
                                    <ReactMarkdown
                                        components={{
                                            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                            strong: ({ children }) => <strong className="font-semibold text-primary">{children}</strong>,
                                            em: ({ children }) => <em className="italic">{children}</em>,
                                        }}
                                    >
                                        {entry.description}
                                    </ReactMarkdown>
                                </div>
                            )}
                        </article>
                    );
                })}
            </div>
        </motion.section>
    );
}
