import { Icons } from "@/components/icons";
import { House, Library } from "lucide-react";
import { Python } from "@/components/ui/svgs/python";
import { Docker } from "@/components/ui/svgs/docker";
import { Kubernetes } from "@/components/ui/svgs/kubernetes";
import { Java } from "@/components/ui/svgs/java";

export const DATA = {
  name: "Mohammed Asir Shahid",
  initials: "AS",
  url: "https://asir.dev",
  location: "Stony Brook, NY",
  locationLink: "https://www.google.com/maps/place/stony+brook+ny",
  description:
    "Engineer-turned-physician. Incoming MD student with a background in mathematics, data science, and automation engineering.",
  summary:
    "I have a BS in Mathematics & Applied Mathematics and Statistics from [Stony Brook University](/#education). After several years working in [data science and automation engineering](/#work), I left my career in tech to pursue medicine. I spent the last three years completing my pre-medical prerequisites at Stony Brook — earning straight As across biology, chemistry, organic chemistry, biochemistry, physics, and anatomy — and I will be starting the [3-Year MD Program with a Radiology Pathway at the Renaissance School of Medicine](/#education) at Stony Brook University in July 2026. My background in quantitative analysis, data, and engineering directly informs my interest in radiology and medical imaging.",
  avatarUrl: "/picofme.png",
  ogImage: "/og_image.png",
  sections: {
    about: { order: 1, enabled: true, heading: "About" },
    work: { order: 2, enabled: true, heading: "Work Experience", presentLabel: "Present" },
    education: { order: 3, enabled: true, heading: "Education" },
    skills: { order: 4, enabled: true, heading: "Skills" },
    projects: {
      order: 5, enabled: true,
      label: "My Projects",
      heading: "Check out my latest work",
      text: "A mix of data science, automation, and homelab projects I've built over the years.",
    },
    hackathons: {
      order: 7, enabled: false,
      label: "Hackathons",
      heading: "I like building things",
      text: "",
    },
    photos: {
      order: 6, enabled: false,
      heading: "Photos",
    },
    contact: {
      order: 8, enabled: true,
      label: "Contact",
      heading: "Get in Touch",
      text: "Want to chat? The fastest way to reach me is by email — I'll respond when I can.",
    },
  },
  photos: [],
  skills: [
    { name: "Python", icon: Python },
    { name: "R" },
    { name: "C" },
    { name: "C++" },
    { name: "Java", icon: Java },
    { name: "SQL" },
    { name: "Linux" },
    { name: "Git" },
    { name: "Docker", icon: Docker },
    { name: "Kubernetes", icon: Kubernetes },
    { name: "Hadoop" },
    { name: "Cloud Computing" },
  ],
  navbar: [
    { href: "/", icon: House, label: "Home" },
    { href: "/blog", icon: Library, label: "Blog" },
  ],
  contact: {
    email: "mohammedshahid@protonmail.com",
    tel: "+1 516 514 5047",
    social: {
      GitHub: {
        name: "GitHub",
        url: "https://github.com/Mohammed-A-Shahid",
        icon: Icons.github,
        navbar: true,
      },
      LinkedIn: {
        name: "LinkedIn",
        url: "https://www.linkedin.com/in/mohammed---shahid/",
        icon: Icons.linkedin,
        navbar: true,
      },
      email: {
        name: "Send Email",
        url: "mailto:mohammedshahid@protonmail.com",
        icon: Icons.email,
        navbar: false,
      },
    },
  },

  work: [
    {
      company: "Zebra Technologies",
      href: "https://www.zebra.com",
      badges: [],
      location: "Holtsville, NY",
      title: "Automation Engineer",
      logoUrl: "https://www.google.com/s2/favicons?domain=zebra.com&sz=128",
      start: "November 2021",
      end: "2022",
      description:
        "Developed and maintained automated testing frameworks to validate hardware and software systems. Wrote Python and shell scripts to streamline QA workflows, reducing manual testing overhead. Collaborated with cross-functional engineering teams on CI/CD pipeline integration and system reliability.",
    },
    {
      company: "Stony Brook University — Applied Mathematics Department",
      href: "https://www.stonybrook.edu/commcms/ams/",
      badges: [],
      location: "Stony Brook, NY",
      title: "Teaching Assistant",
      logoUrl: "https://www.google.com/s2/favicons?domain=stonybrook.edu&sz=128",
      start: "August 2018",
      end: "December 2019",
      description:
        "Teaching Assistant for Linear Algebra and Statistical Laboratory (using R and SAS). Graded assignments and provided personalized feedback to hundreds of students on tight deadlines. Held office hours to host review sessions and walk students through assignments and exam material.",
    },
    {
      company: "Private Tutor",
      href: "",
      badges: [],
      location: "Stony Brook, NY",
      title: "Tutor",
      logoUrl: "https://avatar.vercel.sh/private-tutor?size=40",
      start: "August 2017",
      end: "November 2021",
      description:
        "Tutored college-level Computer Science and Mathematics — Statistics, Linear Algebra, Calculus, and Real Analysis — to fellow university students. Also taught Mathematics, Sciences, and Programming to students from Elementary through High School.",
    },
  ],
  education: [
    {
      school: "Renaissance School of Medicine at Stony Brook University",
      href: "https://renaissance.stonybrookmedicine.edu/",
      degree: "Doctor of Medicine (MD), Candidate — 3-Year MD Program with Radiology Pathway",
      logoUrl: "https://www.google.com/s2/favicons?domain=stonybrookmedicine.edu&sz=128",
      start: "2026",
      end: "2029",
    },
    {
      school: "Stony Brook University",
      href: "https://www.stonybrook.edu/",
      degree: "Pre-Medical Post-Baccalaureate Coursework",
      logoUrl: "https://www.google.com/s2/favicons?domain=stonybrook.edu&sz=128",
      start: "2023",
      end: "2026",
    },
    {
      school: "Stony Brook University",
      href: "https://www.stonybrook.edu/",
      degree: "BS, Mathematics & Applied Mathematics and Statistics",
      logoUrl: "https://www.google.com/s2/favicons?domain=stonybrook.edu&sz=128",
      start: "2017",
      end: "2020",
    },
    {
      school: "MITx",
      href: "https://www.edx.org/course/fundamentals-of-statistics",
      degree: "Fundamentals of Statistics (Certificate)",
      logoUrl: "https://www.google.com/s2/favicons?domain=mit.edu&sz=128",
      start: "2021",
      end: "2021",
    },
    {
      school: "MITx",
      href: "https://www.edx.org/course/probability-the-science-of-uncertainty-and-data",
      degree: "Probability — The Science of Uncertainty and Data (Certificate)",
      logoUrl: "https://www.google.com/s2/favicons?domain=mit.edu&sz=128",
      start: "2021",
      end: "2021",
    },
  ],
  projects: [
    {
      title: "Baseball Stats Dashboard",
      href: "https://baseball.asir.dev",
      dates: "June 2022 - Present",
      active: true,
      description:
        "Web app built with Streamlit in Python for visualizing and exploring Baseball statistics across teams, players, and seasons.",
      technologies: ["Python", "Streamlit", "Pandas", "Data Visualization"],
      links: [
        {
          type: "Website",
          href: "https://baseball.asir.dev",
          icon: <Icons.globe className="size-3" />,
        },
      ],
      image: "",
      video: "",
    },
    {
      title: "Crypto Trading Bot",
      href: "",
      dates: "July 2020 - July 2021",
      active: false,
      description:
        "A profitable cryptocurrency trading bot written in Python using the Coinbase API. Explored extending it with machine-learning-driven signal models.",
      technologies: ["Python", "Coinbase API", "Machine Learning"],
      links: [],
      image: "",
      video: "",
    },
    {
      title: "Puppy Picture Bot",
      href: "",
      dates: "July 2021 - September 2021",
      active: false,
      description:
        "A bot that scrapes top puppy pictures from Reddit using PRAW and periodically texts them to me via the Twilio API.",
      technologies: ["Python", "PRAW", "Twilio"],
      links: [],
      image: "",
      video: "",
    },
    {
      title: "YouTube TikTok Bot",
      href: "https://github.com/Mohammed-A-Shahid/TikTok-Bot",
      dates: "February 2021 - June 2021",
      active: false,
      description:
        "Automated pipeline that downloads top TikToks, stitches them together with ffmpeg, and uploads the compilation to YouTube.",
      technologies: ["Python", "Bash", "ffmpeg", "YouTube API"],
      links: [
        {
          type: "Source",
          href: "https://github.com/Mohammed-A-Shahid/TikTok-Bot",
          icon: <Icons.github className="size-3" />,
        },
      ],
      image: "",
      video: "",
    },
    {
      title: "Personal Website",
      href: "https://asir.dev",
      dates: "April 2021 - Present",
      active: true,
      description:
        "This site. Originally built with Hugo, now rebuilt with Astro v6, React, and Tailwind v4, deployed on Cloudflare.",
      technologies: ["Astro", "React", "TypeScript", "TailwindCSS", "Cloudflare"],
      links: [
        {
          type: "Source",
          href: "https://github.com/AsirShahid/Personal-Website",
          icon: <Icons.github className="size-3" />,
        },
      ],
      image: "",
      video: "",
    },
    {
      title: "Homelab",
      href: "",
      dates: "February 2018 - Present",
      active: true,
      description:
        "Home server running multiple virtual machines for self-hosted services — Nextcloud, Plex, VNC, and Nginx — backed by a MariaDB database, exposed as both a web server and media server.",
      technologies: ["Linux", "KVM", "Nextcloud", "Plex", "Nginx", "MariaDB"],
      links: [],
      image: "",
      video: "",
    },
  ],
  hackathons: [],
} as const;
