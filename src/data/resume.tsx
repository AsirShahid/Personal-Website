import { Icons } from "@/components/icons";
import { House, Library } from "lucide-react";
import { Python } from "@/components/ui/svgs/python";
import { Docker } from "@/components/ui/svgs/docker";
import { Kubernetes } from "@/components/ui/svgs/kubernetes";
import { Java } from "@/components/ui/svgs/java";

export const DATA = {
  name: "Asir Shahid",
  initials: "AS",
  url: "https://asir.dev",
  location: "Selden, NY",
  locationLink: "https://www.google.com/maps/place/selden+ny",
  description:
    "Incoming MD student at the Renaissance School of Medicine, on the 3-Year MD program with a Radiology Pathway. I spent my career before medicine in engineering and data science.",
  summary:
    "I'll be starting the [3-Year MD Program with a Radiology Pathway at the Renaissance School of Medicine](/#education) at Stony Brook University in July 2026. I have a BS in Applied Mathematics and Statistics from [Stony Brook University](/#education), and after working as an [Automation Engineer at Zebra Technologies](/#work) I left engineering to pursue medicine. Over the last few years I've completed my pre-medical prerequisites at Stony Brook, worked as a [Medical Assistant](/#work) and [EMT-B](/#work), and contributed to [computational biochemistry research in the Nagan Lab](/#work). My background in quantitative analysis, data, and engineering directly informs my interest in radiology and medical imaging.",
  avatarUrl: "",
  ogImage: "/og_image.png",
  sections: {
    about: { order: 1, enabled: true, heading: "About" },
    education: { order: 2, enabled: true, heading: "Education" },
    work: { order: 3, enabled: true, heading: "Work Experience", presentLabel: "Present" },
    skills: { order: 4, enabled: true, heading: "Skills" },
    projects: {
      order: 5, enabled: true,
      label: "My Projects",
      heading: "Check out my latest work",
      text: "A mix of medical imaging, computational research, and engineering projects.",
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
      text: "Want to chat? The fastest way is by email. I'll respond when I can.",
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
        url: "https://github.com/AsirShahid",
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

  education: [
    {
      school: "Renaissance School of Medicine at Stony Brook University",
      href: "https://renaissance.stonybrookmedicine.edu/",
      degree: "Doctor of Medicine (MD), Candidate, 3-Year MD Program with Radiology Pathway",
      logoUrl: "https://www.google.com/s2/favicons?domain=stonybrookmedicine.edu&sz=128",
      start: "2026",
      end: "2029",
    },
    {
      school: "Stony Brook University",
      href: "https://www.stonybrook.edu/",
      degree: "BS, Applied Mathematics and Statistics",
      logoUrl: "https://www.google.com/s2/favicons?domain=stonybrook.edu&sz=128",
      start: "2017–2020",
      end: "2023–2026",
    },
  ],

  work: [
    {
      company: "Station Medical",
      href: "",
      badges: [],
      location: "Brentwood, NY",
      title: "Medical Assistant",
      logoUrl: "https://avatar.vercel.sh/station-medical?size=40",
      start: "October 2025",
      end: undefined,
      description:
        "Performed phlebotomy, 12-lead EKGs, and vital signs assessment in a high-volume primary care setting. Facilitated uninterrupted patient care by independently managing prior authorizations and specialty medication appeals to resolve complex insurance coverage disputes.",
    },
    {
      company: "Integrated Spine and Pain Care",
      href: "",
      badges: [],
      location: "Farmingdale, NY",
      title: "Medical Assistant",
      logoUrl: "https://avatar.vercel.sh/integrated-spine-pain?size=40",
      start: "August 2024",
      end: "October 2025",
      description:
        "Facilitated fluoroscopy-guided interventional pain procedures (epidural steroid injections, nerve blocks) by preparing sterile fields, managing instruments, and monitoring patient vitals. Maintained accurate EHR documentation, capturing patient histories and treatment plans to support clinical continuity.",
    },
    {
      company: "Port Jefferson EMS",
      href: "https://www.portjeffersonems.com",
      badges: [],
      location: "Mount Sinai, NY",
      title: "EMT-B",
      logoUrl: "https://avatar.vercel.sh/port-jefferson-ems?size=40",
      start: "October 2024",
      end: "April 2025",
      description:
        "Provided pre-hospital basic life support for medical and trauma emergencies. Commanded emergency scenes, coordinated with paramedic teams, and ensured safe patient transport and handoff to hospital staff.",
    },
    {
      company: "Nagan Lab, Stony Brook University",
      href: "https://www.stonybrook.edu/commcms/chemistry/",
      badges: [],
      location: "Stony Brook, NY",
      title: "Undergraduate Researcher and System Administrator",
      logoUrl: "https://www.google.com/s2/favicons?domain=stonybrook.edu&sz=128",
      start: "October 2023",
      end: undefined,
      description:
        "Investigated force field accuracy for RNA molecular dynamics simulations in AMBER, developing custom Python scripts to analyze stem-loop simulations and validate computational models. Served as System Administrator for the lab's Linux-based computing cluster, writing Bash scripts to automate software deployments, streamline job scheduling, and maintain hardware infrastructure. Co-author on Linzer JT et al., \"Accurately Modeling RNA Stem-Loops in an Implicit Solvent Environment,\" J. Chem. Inf. Model. 2024;64(15):6092–6104.",
    },
    {
      company: "Zebra Technologies",
      href: "https://www.zebra.com",
      badges: [],
      location: "Holtsville, NY",
      title: "Automation Engineer",
      logoUrl: "https://www.google.com/s2/favicons?domain=zebra.com&sz=128",
      start: "August 2020",
      end: "March 2023",
      description:
        "Engineered data processing pipelines using Python and Pandas to parse and analyze large volumes of automated test logs and device telemetry, extracting actionable metrics to identify failure trends. Developed automation frameworks using Python and Selenium to streamline QA, utilizing Matplotlib for data visualization to present root-cause analysis to development teams.",
    },
  ],

  projects: [
    {
      title: "CT Image Reconstruction Pipeline",
      href: "",
      dates: "Fall 2025",
      active: false,
      description:
        "Engineered a geometry-aware filtered back-projection pipeline in Python to reconstruct X-ray CTs from sinogram data. Applied the Radon transform and evaluated reconstructions using structural similarity (SSIM) and peak SNR. Academic project for AMS 325.",
      technologies: ["Python", "NumPy", "SciPy", "Radon Transform", "Image Reconstruction"],
      links: [],
      image: "/ct-sinogram.png",
      video: "",
    },
    {
      title: "Personal Website",
      href: "https://asir.dev",
      dates: "April 2021 - Present",
      active: true,
      description:
        "This site. Originally built with Hugo, now rebuilt with Astro v6, React, and Tailwind v4, deployed on Cloudflare Pages.",
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
        "Home server running multiple virtual machines for self-hosted services including Nextcloud, Plex, VNC, and Nginx, backed by a MariaDB database.",
      technologies: ["Linux", "KVM", "Nextcloud", "Plex", "Nginx", "MariaDB"],
      links: [],
      image: "",
      video: "",
    },
  ],
  hackathons: [],
} as const;
