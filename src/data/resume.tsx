import { Icons } from "@/components/icons";
import { Camera, House } from "lucide-react";
import type { ComponentType, ReactNode } from "react";
import { Python } from "@/components/ui/svgs/python";
import { Docker } from "@/components/ui/svgs/docker";
import { Kubernetes } from "@/components/ui/svgs/kubernetes";
import { R } from "@/components/ui/svgs/r";
import { Git } from "@/components/ui/svgs/git";
import { Linux } from "@/components/ui/svgs/linux";
import { Bash } from "@/components/ui/svgs/bash";
import { Matlab } from "@/components/ui/svgs/matlab";
import { Selenium } from "@/components/ui/svgs/selenium";

interface Skill {
  name: string;
  icon?: ComponentType<{ className?: string }>;
  iconUrl?: string;
}

interface Photo {
  src: string;
  alt: string;
}

interface Hackathon {
  title: string;
  dates: string;
  location: string;
  description: string;
  image?: string;
  links?: readonly { title: string; icon: ReactNode; href: string }[];
}

export const DATA = {
  name: "Asir Shahid",
  initials: "AS",
  url: "https://asir.dev",
  location: "Selden, NY",
  locationLink: "https://www.google.com/maps/place/selden+ny",
  description:
    "Medical student in the Three-Year MD Program at Stony Brook's Renaissance School of Medicine, Class of 2029. Formerly a Data Scientist at Goldman Sachs and an Automation Engineer at Zebra Technologies.",
  summary:
    "I'm a medical student in the [Three-Year MD Program](https://renaissance.stonybrookmedicine.edu/3YMD) at Stony Brook University's [Renaissance School of Medicine](https://renaissance.stonybrookmedicine.edu/), Class of 2029. I earned a BS in [Applied Mathematics and Statistics](https://www.stonybrook.edu/commcms/ams/) at Stony Brook, then worked as an Automation Engineer at Zebra Technologies and a Data Scientist at Goldman Sachs. I changed course because I wanted to work directly with patients. Before starting medical school, I volunteered as an [EMT with Port Jefferson EMS](https://pjems.org), worked as a medical assistant, and conducted [computational biochemistry research in the Nagan Lab](https://sites.google.com/view/mnagan). I'm interested in computational medical imaging, particularly CT reconstruction and quantitative imaging.",
  avatarUrl: "",
  ogImage: "/og_image.png",
  sections: {
    about: { order: 1, enabled: true, heading: "About" },
    education: { order: 2, enabled: true, heading: "Education" },
    work: { order: 3, enabled: true, heading: "Work Experience", presentLabel: "Present" },
    skills: { order: 4, enabled: true, heading: "Skills" },
    projects: {
      order: 5, enabled: true,
      label: "Projects",
      heading: "Research and coursework",
      text: "",
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
      text: "Email is the best way to reach me.",
    },
  },
  photos: [] as readonly Photo[],
  skills: [
    { name: "Python", icon: Python },
    { name: "R", icon: R },
    { name: "Matlab", icon: Matlab },
    { name: "SQL", iconUrl: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/azuresqldatabase/azuresqldatabase-original.svg" },
    { name: "NumPy", iconUrl: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/numpy/numpy-original.svg" },
    { name: "SciPy", iconUrl: "https://www.google.com/s2/favicons?domain=scipy.org&sz=128" },
    { name: "Jupyter", iconUrl: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/jupyter/jupyter-original.svg" },
    { name: "Pandas", iconUrl: "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/pandas/pandas-original.svg" },
    { name: "Bloomberg", iconUrl: "https://www.google.com/s2/favicons?domain=bloomberg.com&sz=128" },
    { name: "Bash", icon: Bash },
    { name: "Linux", icon: Linux },
    { name: "Git", icon: Git },
    { name: "Docker", icon: Docker },
    { name: "Kubernetes", icon: Kubernetes },
    { name: "Selenium", icon: Selenium },
    { name: "Cloud Computing" },
  ] as readonly Skill[],
  navbar: [
    { href: "/", icon: House, label: "Home" },
    { href: "/outside", icon: Camera, label: "/outside" },
  ],
  contact: {
    email: "mohammedshahid@protonmail.com",
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
      ORCID: {
        name: "ORCID",
        url: "https://orcid.org/0009-0009-6232-387X",
        icon: Icons.orcid,
        navbar: false,
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
      degree: "Doctor of Medicine (MD), Candidate, Three-Year MD Program",
      logoUrl: "https://www.google.com/s2/favicons?domain=stonybrook.edu&sz=128",
      start: "2026",
      end: "2029",
    },
    {
      school: "Stony Brook University",
      href: "https://www.stonybrook.edu/",
      degree: "BS, Applied Mathematics and Statistics",
      logoUrl: "https://www.google.com/s2/favicons?domain=stonybrook.edu&sz=128",
      start: "2017–2020, 2023–2026",
      end: undefined,
    },
  ],

  work: [
    {
      company: "Wang Neuroimaging Lab, Stony Brook University",
      href: "https://renaissance.stonybrookmedicine.edu/radiology/research/laboratories/Yicun-Wang",
      badges: [],
      location: "Stony Brook, NY",
      title: "Incoming Research Student",
      logoUrl: "https://www.google.com/s2/favicons?domain=stonybrook.edu&sz=128",
      start: "2026",
      end: "",
      description:
        "Joining a study that compares patients with idiopathic normal pressure hydrocephalus (iNPH) to matched controls. It measures arterial, venous, and CSF flow with real-time phase-contrast MRI, along with brain tissue motion and CSF pulsation in the subarachnoid space. The aim is better markers for diagnosing iNPH and deciding who should get a shunt.",
    },
    {
      company: "Station Medical",
      href: "https://station-medical.com",
      badges: [],
      location: "Brentwood, NY",
      title: "Medical Assistant",
      logoUrl: "https://www.google.com/s2/favicons?domain=station-medical.com&sz=128",
      start: "October 2025",
      end: "May 2026",
      description:
        "Drew blood, ran 12-lead EKGs, and took vitals at a busy primary care practice. Handled prior authorizations and specialty medication appeals on my own.",
    },
    {
      company: "Nagan Lab, Stony Brook University",
      href: "https://sites.google.com/view/mnagan",
      badges: [],
      location: "Stony Brook, NY",
      title: "Undergraduate Researcher and System Administrator",
      logoUrl: "https://www.google.com/s2/favicons?domain=stonybrook.edu&sz=128",
      start: "October 2023",
      end: "July 2026",
      description:
        "Tested how accurately AMBER force fields reproduce RNA stem-loop structures in molecular dynamics simulations, and wrote Python scripts to analyze the runs. Also ran the lab's Linux cluster: Bash scripts for software installs and job scheduling, and upkeep of the hardware.",
    },
    {
      company: "Integrated Spine and Pain Care",
      href: "",
      badges: [],
      location: "Farmingdale, NY",
      title: "Medical Assistant",
      logoUrl: "/ispc.png",
      start: "August 2024",
      end: "October 2025",
      description:
        "Assisted with fluoroscopy-guided pain procedures such as epidural steroid injections and nerve blocks: set up sterile fields, handled instruments, and monitored vitals. Documented patient histories and treatment plans in the EHR.",
    },
    {
      company: "Port Jefferson EMS",
      href: "https://pjems.org",
      badges: [],
      location: "Mount Sinai, NY",
      title: "EMT-B",
      logoUrl: "/pjems.png",
      start: "October 2024",
      end: "April 2025",
      description:
        "Provided basic life support on medical and trauma calls. Led scenes, worked with paramedic crews, and transported patients and handed them off to hospital staff.",
    },
    {
      company: "Goldman Sachs",
      href: "https://www.goldmansachs.com",
      badges: [],
      location: "Philadelphia, PA",
      title: "Data Scientist",
      logoUrl: "https://www.google.com/s2/favicons?domain=goldmansachs.com&sz=128",
      start: "February 2023",
      end: "July 2023",
      description:
        "Built quantitative models and data pipelines in Python, NumPy, SciPy, and SQL for trading algorithm research. Ran statistical and time series analyses on Bloomberg data and shared the results with trading teams in Jupyter notebooks.",
    },
    {
      company: "Zebra Technologies",
      href: "https://www.zebra.com",
      badges: [],
      location: "Holtsville, NY",
      title: "Automation Engineer",
      logoUrl: "https://www.google.com/s2/favicons?domain=zebra.com&sz=128",
      start: "August 2020",
      end: "February 2023",
      description:
        "Wrote Python and Pandas pipelines that parsed automated test logs and device telemetry to find failure trends. Built Selenium test automation for QA and used Matplotlib charts to show developers the root causes of failures.",
    },
  ],

  projects: [
    {
      title: "RNA Stem-Loop Force Field Research",
      href: "https://doi.org/10.1021/acs.jcim.4c00756",
      dates: "2024",
      active: false,
      description:
        "Co-author on a study of how well AMBER force fields with implicit solvent reproduce RNA stem-loop structures. Matching the experimental loop structures took CH···O force field modifications plus a nonpolar solvent correction. Published in the Journal of Chemical Information and Modeling.",
      technologies: ["Python", "AMBER", "Molecular Dynamics", "RNA", "Implicit Solvent", "Bash"],
      links: [
        {
          type: "Paper",
          href: "https://doi.org/10.1021/acs.jcim.4c00756",
          icon: <Icons.globe className="size-3" />,
        },
      ],
      image: "/chiol3.gif",
      video: "",
    },
    {
      title: "CT Image Reconstruction Pipeline",
      href: "",
      dates: "Fall 2025",
      active: false,
      description:
        "Course project for AMS 325: filtered back-projection in Python that reconstructs CT images from sinograms, using the Radon transform, with reconstructions scored by SSIM and peak SNR.",
      technologies: ["Python", "NumPy", "SciPy", "Radon Transform", "Image Reconstruction"],
      links: [],
      image: "/sinogram.png",
      video: "",
    },
  ],
  hackathons: [] as readonly Hackathon[],
} as const;
