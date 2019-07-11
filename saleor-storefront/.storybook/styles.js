import styled from "styled-components";

export const Wrapper = styled.div`
  position: relative;
  margin: 20px;
`;

export const Outline = styled.div`
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid rgba(0, 0, 0, 0.2);
  top: 0;
  left: 0;
  pointer-events: none;
  box-sizing: border-box;
`;
