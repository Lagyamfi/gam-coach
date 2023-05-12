<script>
  //@ts-check
  import '../../typedef';
  import Coach from '../coach/Coach.svelte';
  import DiffPicker from '../DiffPicker.svelte';
  import ConfirmModal from '../confirm-modal/ConfirmModal.svelte';
  import InputForm from '../input-form/InputForm.svelte';
  import BookmarkPanel from '../bookmark-panel/BookmarkPanel.svelte';
  import Tooltip from '../Tooltip.svelte';

  import d3 from '../../utils/d3-import';
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';
  import { fade, fly } from 'svelte/transition';
  import {
    tooltipConfigStore,
    inputFormConfigStore,
    constraintsStore,
    bookmarkConfigStore,
    ebmStore
  } from '../../store';
  import { Constraints } from '../coach/Coach';
  import { random } from '../../utils/utils';

  import pointArrowSVG from '../../img/point-arrow.svg';
  import iconRefreshSVG from '../../img/icon-refresh3.svg';
  import iconEditSVG from '../../img/icon-edit.svg';
  import iconGithub from '../../img/icon-github.svg';
  import iconGT from '../../img/icon-gt.svg';
  import iconMS from '../../img/icon-ms.svg';
  //import iconCEA from '../../img/CEA_List.svg';
  import iconCopy from '../../img/icon-copy-box.svg';
  import iconCheckBox from '../../img/icon-check-box.svg';
  import iconPdf from '../../img/icon-pdf.svg';

  // Import samples
  import samplesCustomer from '../../config/data/customer-classifier-random-samples.json';

  export let modelName = 'customer';

  let curSamples = samplesCustomer;
  let curIndex = 126;

  let bibtexCopied = false;
  let bibtexHovering = false;

  const datasetOptions = [
    { name: 'customer', display: "Customer Churn" },
  ];

  const cfMethodOptions = [
    {name: 'dice', display: 'Dice'},
    {name: 'coach', display: 'COACH'},
  ];

  let cfMethod = 'dice';

  const initModelInfo = () => {
    switch (modelName) {
      case 'customer': {
        curSamples = samplesCustomer;
        curIndex = curIndex;
        break;
      }
      default: {
        console.warn('Unknown model name');
        curSamples = samplesCustomer;
        modelName = 'customer';
        curIndex = 126;
      }
    }
  };

  const getAgencyName = (modelName) => {
    if (modelName === 'compas') {
      return 'court';
    } else if (modelName === 'crime-full' || modelName === 'crime') {
      return 'funding agency';
    } else {
      return 'bank';
    }
  };

  const getApplicantName = (modelName) => {
    if (modelName === 'compas') {
      return 'a bail applicant';
    } else if (modelName === 'crime-full' || modelName === 'crime') {
      return 'applying for grants for county';
    } else {
      return 'a loan applicant';
    }
  };

  // localhost:5005/?dataset=compas
  const urlParams = new URLSearchParams(window.location.search);
  console.log(urlParams);
  const urlModelName = urlParams.get('dataset');
  const validModelNames = new Set([
    'customer',
  ]);
  if (urlModelName !== null && validModelNames.has(urlModelName)) {
    modelName = urlModelName;
  }

  initModelInfo();

  const unsubscribes = [];
  let windowLoaded = false;
  let currentPlayer = null;

  const indexFormatter = d3.format('03d');

  let verificationCode = null;
  let buttonText = "I'm Done!";
  let updated = false;

  // Initialize the logger
  const logger = null;

  // curIndex = random(0, curSamples.length - 1);
  let curExample;
  getExample(curIndex).then((data) => {
    curExample = data;
  });

  const pointArrowSVGProcessed = pointArrowSVG.replaceAll(
    'white',
    'currentcolor'
  );

  // Set up tooltip
  let tooltip = null;
  let tooltipConfig = null;
  unsubscribes.push(
    tooltipConfigStore.subscribe((value) => {
      tooltipConfig = value;
    })
  );

  /** @type {Constraints} */
  let constraints = null;
  unsubscribes.push(
    constraintsStore.subscribe((value) => {
      constraints = value;
    })
  );

  /** @type {BookmarkConfig} */
  let bookmarkConfig = null;
  unsubscribes.push(
    bookmarkConfigStore.subscribe((value) => {
      bookmarkConfig = value;
    })
  );

  /** @type {InputFormConfig} */
  let inputFormConfig = null;
  unsubscribes.push(
    inputFormConfigStore.subscribe((value) => {
      inputFormConfig = value;

      // Update curExample if it is changed
      if (inputFormConfig.action === 'saved') {
        inputFormConfig.action = null;
        updated = true;
        curExample = inputFormConfig.curExample;
        inputFormConfigStore.set(inputFormConfig);
      }
    })
  );

  /**
   * @param {number} idx
   */
  async function getExample(idx) {
  try {
    const response = await fetch(`http://127.0.0.1:8000/dataset/${idx}`);

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching data:", error);
    throw error;
  }
}

  const refreshClicked = async () => {
    // Resample the cur example
    curIndex = random(0, curSamples.length - 1);
    // fetch newExample from python wep server
    const newExample = await getExample(curIndex);
    updated = false;
    curExample = newExample;

    // console.log(logger?.toJSON());
  };

  const optionClicked = (e, option) => {
    if (option.name === modelName) return;

    ebmStore.set({});
    inputFormConfigStore.set({
      show: false,
      ebm: null,
      features: null,
      plansInfo: null,
      curExample: [],
      action: null
    });
    bookmarkConfigStore.set({
      show: false,
      features: null,
      plans: new Map(),
      focusOutTime: 0,
      plansInfo: null
    });
    updated = false;

    modelName = option.name;
    initModelInfo();
    curExample = curSamples[curIndex];
  };

  const cfMethodOptionsClicked =(e, option) => {
    if (option.name === cfMethod) return;

    cfMethod = option.name;
    constraints.cfMethod = cfMethod;
  };

  const editClicked = () => {
    inputFormConfig.show = true;
    inputFormConfig.curExample = curExample;
    inputFormConfig.action = null;
    inputFormConfigStore.set(inputFormConfig);
  };

  onMount(() => {
    // window.onload = () => { windowLoaded = true; };
    windowLoaded = true;
  });

  onDestroy(() => {
    unsubscribes.forEach((unsub) => unsub());
  });
</script>

<div class="page">
  <Tooltip bind:this={tooltip} />

  <div class="top" id="top">
    <div class="top-fill" />

    <div class="top-empty" />

    <div class="coach-left">
      <!-- <div class='help-arrow'>{@html pointArrowSVGProcessed}</div> -->
      <div class="help-note">
        <div class="arrow" />
        <div class="title-top">Imagine...</div>
        <div class="title">
          You're {getApplicantName(modelName)}
        </div>
        <div class="input-number">
          <div
            class="svg-icon"
            title="Edit the input values"
            on:click={() => editClicked()}
          >
            {@html iconEditSVG}
          </div>
          <div
            class="svg-icon"
            title="Try a random input sample"
            on:click={() => refreshClicked()}
          >
            {@html iconRefreshSVG}
          </div>
          <div class="number">
            #{indexFormatter(curIndex)}{updated ? '*' : ''}
          </div>
        </div>
        <div class="description">
          <span class="line"> Your application is rejected </span>
          <div class="help-arrow">{@html pointArrowSVGProcessed}</div>
          <span class="line">
            The {getAgencyName(modelName)} points you to
          </span>
          <span class="line">
            <strong>GAM Coach</strong> to help you
          </span>
          <span class="line"> succeed in next application </span>
        </div>
      </div>
    </div>

    <div class="coach-right">
      <div class="icon-container">
        <a target="_blank" href="https://github.com/xiaohk/gam-coach/">
          <div class="svg-icon" title="Open-source code">
            {@html iconGithub}
          </div>
          <span>Code</span>
        </a>
      </div>
      <div class="dataset-menu">
        <span class="dataset-description">Choose a dataset</span>
        {#each datasetOptions as option, i}
          <div
            class="dataset-option"
            class:selected={option.name === modelName ||
              (option.name === 'crime' && modelName === 'crime-full')}
            on:click={(e) => optionClicked(e, option)}
          >
            <div class="dataset-place" />
            <span class="dataset-name">{option.display}</span>
          </div>
        {/each}
      </div>

      <div class="dataset-menu">
        <span class="dataset-description">Choose CF method</span>
        {#each cfMethodOptions as option, i}
          <div
            class="dataset-option"
            class:selected={option.name === cfMethod}
            on:click={(e) => cfMethodOptionsClicked(e, option)}
          >
            <div class="dataset-place" />
            <span class="dataset-name">{option.display}</span>
          </div>
        {/each}
      </div>

    </div>

    {#key curExample}
      <div class="coach-wrapper">
        <Coach {windowLoaded} {curExample} {logger} {modelName} {cfMethod}/>
      </div>
    {/key}

    <DiffPicker {logger} />
    <ConfirmModal />

    {#key modelName}
      <InputForm />
    {/key}

    {#key modelName}
      <BookmarkPanel {windowLoaded} {logger} />
    {/key}
  </div>


  <div class="article-footer">
    <div class="footer-main">
      <div class="footer-logo">
        <a target="_blank" href="https://www.gatech.edu/">
          <div class="svg-icon icon-gt" title="Georgia Tech">
            <!-- {@html iconCEA} -->
          </div>
        </a>

        <a target="_blank" href="https://www.microsoft.com/en-us/research/">
          <div class="svg-icon icon-ms" title="Microsoft Research">
            {@html iconMS}
          </div>
        </a>
      </div>
    </div>
  </div>
</div>

<style lang="scss">
  @import './Article.scss';
</style>
