/**
 * icons.tsx — Bytech LP SVG Components
 *
 * Extracted from RAW_SVGS.json (docs/research/RAW_SVGS.json).
 * All SVGs are deduplicated and named by visual function.
 *
 * Section divider shapes (ShapeWedge*, ShapeSlant, ShapeWave) are used as
 * decorative dividers between LP sections.
 * Icon* components are UI icons (nav arrows, plus, scroll indicator).
 */

import type { SVGProps } from "react";

// ── Section divider shapes ────────────────────────────────────────────────

/**
 * ShapeWedgeDown
 * A chevron/wedge shape pointing downward, used as a section divider.
 * path: M500,98.9L0,6.1V0h1000v6.1L500,98.9z
 */
export function ShapeWedgeDown(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 1000 100"
      preserveAspectRatio="none"
      aria-hidden="true"
      {...props}
    >
      <path d="M500,98.9L0,6.1V0h1000v6.1L500,98.9z" />
    </svg>
  );
}

/**
 * ShapeSlant
 * A diagonal slant shape, used as a section divider (left-to-right slope).
 * path: M0,6V0h1000v100L0,6z
 */
export function ShapeSlant(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 1000 100"
      preserveAspectRatio="none"
      aria-hidden="true"
      {...props}
    >
      <path d="M0,6V0h1000v100L0,6z" />
    </svg>
  );
}

/**
 * ShapeWave
 * A soft wave/arch shape pointing upward, used as a section divider.
 * path: M500.2,94.7L0,0v100h1000V0L500.2,94.7z
 */
export function ShapeWave(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 1000 100"
      preserveAspectRatio="none"
      aria-hidden="true"
      {...props}
    >
      <path d="M500.2,94.7L0,0v100h1000V0L500.2,94.7z" />
    </svg>
  );
}

// ── UI Icons ──────────────────────────────────────────────────────────────

/**
 * IconPlus
 * Plus / add icon (Font Awesome fas-plus).
 * Used in FAQ accordion open/close trigger.
 */
export function IconPlus(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 448 512"
      aria-hidden="true"
      {...props}
    >
      <path d="M416 208H272V64c0-17.67-14.33-32-32-32h-32c-17.67 0-32 14.33-32 32v144H32c-17.67 0-32 14.33-32 32v32c0 17.67 14.33 32 32 32h144v144c0 17.67 14.33 32 32 32h32c17.67 0 32-14.33 32-32V304h144c17.67 0 32-14.33 32-32v-32c0-17.67-14.33-32-32-32z" />
    </svg>
  );
}

/**
 * IconChevronLeft
 * Left-pointing chevron (Elementor eicon-chevron-left).
 * Used in carousel/slider previous button.
 */
export function IconChevronLeft(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 1000 1000"
      aria-hidden="true"
      {...props}
    >
      <path d="M646 125C629 125 613 133 604 142L308 442C296 454 292 471 292 487 292 504 296 521 308 533L604 854C617 867 629 875 646 875 663 875 679 871 692 858 704 846 713 829 713 812 713 796 708 779 692 767L438 487 692 225C700 217 708 204 708 187 708 171 704 154 692 142 675 129 663 125 646 125Z" />
    </svg>
  );
}

/**
 * IconChevronRight
 * Right-pointing chevron (Elementor eicon-chevron-right).
 * Used in carousel/slider next button.
 */
export function IconChevronRight(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 1000 1000"
      aria-hidden="true"
      {...props}
    >
      <path d="M696 533C708 521 713 504 713 487 713 471 708 454 696 446L400 146C388 133 375 125 354 125 338 125 325 129 313 142 300 154 292 171 292 187 292 204 296 221 308 233L563 492 304 771C292 783 288 800 288 817 288 833 296 850 308 863 321 871 338 875 354 875 371 875 388 867 400 854L696 533Z" />
    </svg>
  );
}

/**
 * IconDoubleAngleDown
 * Double chevron-down icon (Font Awesome fas-angle-double-down).
 * Used as a scroll-down indicator.
 */
export function IconDoubleAngleDown(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 320 512"
      aria-hidden="true"
      {...props}
    >
      <path d="M143 256.3L7 120.3c-9.4-9.4-9.4-24.6 0-33.9l22.6-22.6c9.4-9.4 24.6-9.4 33.9 0l96.4 96.4 96.4-96.4c9.4-9.4 24.6-9.4 33.9 0L313 86.3c9.4 9.4 9.4 24.6 0 33.9l-136 136c-9.4 9.5-24.6 9.5-34 .1zm34 192l136-136c9.4-9.4 9.4-24.6 0-33.9l-22.6-22.6c-9.4-9.4-24.6-9.4-33.9 0L160 352.1l-96.4-96.4c-9.4-9.4-24.6-9.4-33.9 0L7 278.3c-9.4 9.4-9.4 24.6 0 33.9l136 136c9.4 9.5 24.6 9.5 34 .1z" />
    </svg>
  );
}
