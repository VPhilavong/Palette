'use client';

import Image from "next/image";

type UserProfileProps = {
  /**
   * Full name of the user
   */
  name: string;
  /**
   * User's job title or role
   */
  role: string;
  /**
   * User's profile image (static import or URL)
   */
  imageSrc: string;
  /**
   * Short bio or description
   */
  bio?: string;
  /**
   * List of user social links (label, href, emoji icon)
   */
  socials?: {
    label: string;
    href: string;
    icon: string;
  }[];
  /**
   * Optional list of tags/skills
   */
  tags?: string[];
  /**
   * Loading state
   */
  loading?: boolean;
  /**
   * Error message (if loading fails)
   */
  error?: string;
};

export default function UserProfilePage({
  name = "John Doe",
  role = "Software Engineer",
  imageSrc = "https://ui-avatars.com/api/?background=random&name=John+Doe",
  bio = "Passionate developer building amazing user experiences",
  socials = [
    { label: "GitHub", href: "https://github.com", icon: "💻" },
    { label: "LinkedIn", href: "https://linkedin.com", icon: "💼" },
    { label: "Twitter", href: "https://twitter.com", icon: "🐦" }
  ],
  tags = ["React", "TypeScript", "Node.js"],
  loading = false,
  error,
}: UserProfileProps) {
  if (loading) {
    return (
      <section
        className="flex flex-col items-center justify-center min-h-[50vh] bg-gray-100 w-full animate-pulse"
        aria-busy="true"
        aria-live="polite"
      >
        <div className="rounded-full bg-gray-200 w-24 h-24 mb-6" />
        <div className="h-4 bg-gray-200 rounded w-40 mb-2" />
        <div className="h-3 bg-gray-200 rounded w-28 mb-4" />
        <div className="h-3 bg-gray-200 rounded w-64 mb-2" />
        <div className="h-3 bg-gray-200 rounded w-52" />
      </section>
    );
  }

  if (error) {
    return (
      <section
        className="flex flex-col items-center justify-center min-h-[50vh] bg-gray-100 w-full"
        role="alert"
        aria-live="assertive"
      >
        <div className="rounded-full bg-red-500 w-24 h-24 flex items-center justify-center mb-6">
          <span className="text-4xl" aria-hidden>
            ⚠️
          </span>
        </div>
        <p className="text-base font-semibold text-gray-900 mb-2">
          Error loading profile
        </p>
        <p className="text-sm text-gray-600">{error}</p>
      </section>
    );
  }

  return (
    <section
      className="w-full min-h-[70vh] flex flex-col items-center justify-center px-4 py-8 bg-sky-500/10 backdrop-blur-md"
      aria-label={`${name} profile`}
    >
      <div className="w-full max-w-xl bg-white/80 rounded-xl shadow-lg flex flex-col items-center px-8 py-12 gap-6 transition-all duration-300 hover:shadow-xl">
        <div className="relative">
          <Image
            src={imageSrc}
            alt={`${name} profile picture`}
            width={112}
            height={112}
            className="rounded-full shadow-md border-4 border-blue-600 bg-gray-100 object-cover transition-all duration-300 hover:scale-105"
            priority
          />
          <span
            className="absolute bottom-0 right-0 bg-emerald-600 rounded-full w-6 h-6 flex items-center justify-center ring-4 ring-white text-xs font-bold transition-all duration-200"
            aria-label="Online"
            title="Online"
          >
            🟢
          </span>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 text-center">{name}</h1>
        <h2 className="text-base font-semibold text-blue-600 text-center">
          {role}
        </h2>
        {bio && (
          <p className="text-base text-gray-600 text-center mt-2 mb-2">
            {bio}
          </p>
        )}

        {tags && tags.length > 0 && (
          <ul className="flex flex-wrap gap-2 justify-center mt-2" aria-label="Skills and tags">
            {tags.map((tag) => (
              <li
                key={tag}
                className="text-xs font-medium text-emerald-600 bg-emerald-50 rounded-md px-2 py-1"
              >
                {tag}
              </li>
            ))}
          </ul>
        )}

        {socials && socials.length > 0 && (
          <nav
            className="flex gap-4 mt-4"
            aria-label="Social links"
          >
            {socials.map(({ label, href, icon }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center gap-2 text-base text-indigo-600 rounded-full p-2 transition-all duration-200 hover:bg-indigo-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                aria-label={label}
                tabIndex={0}
              >
                <span className="text-lg transition-transform duration-200 group-hover:scale-110">
                  {icon}
                </span>
                <span className="text-sm font-semibold hidden sm:inline">{label}</span>
              </a>
            ))}
          </nav>
        )}
      </div>
    </section>
  );
}