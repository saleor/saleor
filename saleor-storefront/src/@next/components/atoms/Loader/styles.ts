import { styled } from "@styles";
import { keyframes } from "styled-components";

import { getContentWindowHeight } from "@utils/styles";

const firstItem = keyframes`
  0% {
    left: 0;
  }
  12.5% {
    left: 2rem;
  }
  25% {
    left: 4rem;
  }
  37.5% {
    left: 2rem;
  }
  50% {
    left: 0;
  }
  100% {
    left: 0;
  }
`;

const secondItem = keyframes`
  0% {
    left: 2rem;
  }
  12.5% {
    left: 2rem;
  }
  25% {
    left: 4rem;
  }
  37.5% {
    left: 2rem;
  }
  62.5% {
    left: 2rem;
  }
  75% {
    left: 0;
  }
  87.5% {
    left: 2rem;
  }
  100% {
    left: 2rem;
  }
`;

const thirdItem = keyframes`
  0% {
    left: 4rem;
  }
  50% {
    left: 4rem;
  }
  62.5% {
    left: 2rem;
  }
  75% {
    left: 0;
  }
  87.5% {
    left: 2rem;
  }
  100% {
    left: 4rem;
  }
`;

export const Wrapper = styled.div<{ fullScreen: boolean }>`
  display: flex;
  align-items: center;
  width: 100%;
  height: ${props =>
    props.fullScreen ? `${getContentWindowHeight()}px` : "100%"};
  padding: ${props => props.theme.spacing.spacer} 0;
`;

export const Items = styled.div`
  position: relative;
  width: 5rem;
  height: 1rem;
  margin: 0 auto;

  span {
    background-color: ${props => props.theme.colors.secondary};
    width: 1rem;
    height: 1rem;
    border-radius: 1rem;
    position: absolute;

    &:nth-child(1) {
      left: 0;
      animation: ${firstItem} 2s infinite;
      animation-timing-function: linear;
    }

    &:nth-child(2) {
      left: 2rem;
      animation: ${secondItem} 2s infinite;
      animation-timing-function: linear;
    }

    &:nth-child(3) {
      right: 0;
      animation: ${thirdItem} 2s infinite;
      animation-timing-function: linear;
    }
  }
`;
