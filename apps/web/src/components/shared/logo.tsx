import { useId, type HTMLAttributes, type SVGProps } from "react";

import { cn } from "@/lib/utils";

/**
 * The mark, inline so it needs no request and scales with `className`.
 * The same drawing as app/icon.svg. Gradient ids are prefixed with `useId`
 * so two marks on one page do not share them.
 */
export function Logo(props: SVGProps<SVGSVGElement>) {
  const id = useId();
  const url = (name: string) => `url(#${id}-${name})`;
  return (
    <svg viewBox="208 122.5 840 840" aria-hidden="true" {...props}>
      <defs>
        <linearGradient
          id={`${id}-navy`}
          x1="300"
          y1="330"
          x2="880"
          y2="860"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#0b2925" />
          <stop offset="1" stopColor="#09231f" />
        </linearGradient>
        <linearGradient
          id={`${id}-face`}
          x1="470"
          y1="400"
          x2="720"
          y2="760"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#14604d" />
          <stop offset="1" stopColor="#0e493c" />
        </linearGradient>
        <linearGradient
          id={`${id}-top`}
          x1="560"
          y1="235"
          x2="802"
          y2="395"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#6bd1a4" />
          <stop offset="1" stopColor="#31a276" />
        </linearGradient>
        <linearGradient
          id={`${id}-blue`}
          x1="720"
          y1="365"
          x2="900"
          y2="570"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#269c73" />
          <stop offset="1" stopColor="#16664f" />
        </linearGradient>
        <linearGradient
          id={`${id}-right`}
          x1="850"
          y1="580"
          x2="1000"
          y2="740"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#155c4c" />
          <stop offset="1" stopColor="#104737" />
        </linearGradient>
        <linearGradient
          id={`${id}-lower`}
          x1="482"
          y1="745"
          x2="650"
          y2="835"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#3cae82" />
          <stop offset="1" stopColor="#278a67" />
        </linearGradient>
        <linearGradient
          id={`${id}-bottom`}
          x1="650"
          y1="750"
          x2="889"
          y2="860"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="#114c3b" />
          <stop offset="1" stopColor="#248663" />
        </linearGradient>
      </defs>
      <path
        fill={url("navy")}
        d="M570 227 730 272 808 380 864 414 915 531 986 615 1000 730 919 829 889 858H406L330 800 256 687 317 483 413 407 447 322Z"
      />
      <path fill={url("top")} d="M570 227 730 272 808 380 864 414 724 362 585 282Z" />
      <path
        fill={url("face")}
        d="M585 282 724 362 689 449 627 414 476 500 476 509 674 509 650 592 650 684 649 745 443 766 422 684 406 588 394 501 477 432 566 302Z"
      />
      <path fill={url("blue")} d="M724 362 864 414 881 567 856 532 751 433Z" />
      <path fill="#247c5b" d="M864 414 915 531 881 567Z" />
      <path fill="#81d7af" d="M915 531 986 615 881 567Z" />
      <path fill="#4db88e" d="M915 531 938 558 881 567Z" />
      <path fill={url("right")} d="M881 567 986 615 1000 730 882 766 835 695 832 637Z" />
      <path fill="#258363" d="M881 567 832 637 809 638Z" />
      <path fill="#32a479" d="M317 483 349 458 474 431 479 433 394 501Z" />
      <path fill="#1c7254" d="M406 588 422 684 341 679 376 627Z" />
      <path fill={url("lower")} d="M477 762 649 745 582 836 552 817 518 793Z" />
      <path fill="#15513c" d="M649 745 657 798 582 836Z" />
      <path fill={url("bottom")} d="M649 745 827 770 889 858 851 858 756 807 657 798Z" />
      <g fill="#fdf9f2">
        <path d="M476 500 627 414 778 500V509H476Z" />
        <path
          fillRule="evenodd"
          d="M494 529H760V549H747L741 556V684H764V715H788V746H811V766L649 745 443 766V746H466V715H490V684H514V556L508 549H494ZM566 549 559 556V684H605V556L598 549ZM657 549 650 556V684H695V556L688 549Z"
        />
      </g>
    </svg>
  );
}

/** The "GOV-MINE" wordmark in the logo face (Barlow Condensed, set in app/layout.tsx). */
export function Wordmark({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn("font-logo leading-none font-semibold tracking-[0.18em] uppercase", className)}
      {...props}
    >
      gov-mine
    </span>
  );
}
