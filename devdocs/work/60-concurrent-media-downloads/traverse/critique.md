# Critique — finite owned media windows
## User Input
_branch.md, sensemakingSV6, decompositionP1–P5 and innovation candidates/assemblyS.
## Dimensions (extracted; fixed through evaluation)
D1 critical compatibility: user's 'default ... one by one ... as now' means no new
source lookahead/tasks/error policy at1, not merely max-active=1.
D2 critical progress truth: actual MessageBatch next_after_id equals last fully
prepared ordered record; source IDs need not be contiguous. Saved receipt semantics
must survive failure101 after successes102/103.
D3 critical physical ownership: child termination must include owned file/SDK borrow
cleanup; actual sdk_lifetimes.json reports cancelled borrowed1/returned0. Repeated
caller stop cannot destroy the settlement handle.
D4 critical source/account policy: no worker retry storm, account switch or mutable
client thresholds; actual SDK retries/internal waits/cached waits and pool threshold0
must retain meaning. Identity is not guessed from session/cache.
D5 critical observation and bounds: only explicitly owned tasks inherit attribution;
queued/unaccepted work bounded; callback/replay cannot cause unnoticed later writes.
D6 high scope/feasibility: feature must work at bothreaders and runtime consumers
without account/globalstorage redesign; local extent must be explicit.
D7 high evidence: real SDK/public-reader/nativefiles checks before adoption, no
stand-in that supplies ownership behavior. Live throughput remains unproven.
D8 medium efficiency: useful small overlap, bounded memory; perfect utilization
not critical if fixed windows materially overlap waits. This is not a max-speed promise.
Frame premises prosecuted separately: if default1 couldchange, global rewrite looks
simpler but violates explicituseranchor; if prefix unnecessary, maxIDwins but actual
acknowledge_sync then permanently skipsgap; if taskdone equalsresourcecleanup, actual
SDKprobe falsifies it. Dimensions cover failure planes, not onlylabels. No criterion
requires inducing real rate limits to validate handling.
## Landscape and candidate collisions (iteration1)
P1G/A globalregistry: prosecution needs verifiedaccount identity, differingN policies,
mixeddefaultcall rules and cleanup beyondcurrentengine; defense trueaccountaggregate
couldprotectmanyconsumers. Collision: boundary/future, REFINE into explicitfuturetask
when independent same-account engines require sharedadmission; not prerequisite here.
P1F engineownership: prosecution wait-lock deadlocks when callback reenters; defense
sameengine owns allitsclients, narrower thannewaccountauthority. Collision: SURVIVE
with its existing reject variant (one opted-in media operation/engine; reject a second
before sourcework). N1/independentengines explicitly caller-coordinated; no globalcap.
P1C percallonly: prosecution twoN3 calls silentlyadmit6; defense ordinarypercallAPI is
simple. Collision: REFINE toP1F for opted-in sameengine; publicscope stays honest.
P2G/Q rollingwindow: prosecution firsthung while lateritems keeprefilling can mask
stall despiteactivecap; defense improvesutilization. Collision: boundary, REFINE by
bounding unretiredwindow/perfiletimeouts; defer until measuredneed (D8 noncritical).
P2F/W/B/R finitewindow: prosecution completedlaterfiles and callbacks leave tasks at
yieldpoints; defense no refilluntilwindowsettles givesfinite work. Collision: SURVIVE
only with explicit context ownership that settlesbefore callbackboundary/exit and
keeps orderedacceptance separate. AtomSDKborrow must be recorded and returned even
ifSDKerror bypasses iterator.close; CDN-ownedhelpers must settle likewise.
P2C trustSDKcleanup: prosecution actual cancelledborrow notreturned; defense SDK is
maintainedshareddependency. Collision: KILL D3; seed explicitownership of resources
createdby opted-in download span, not changing allsequentialSDKbehavior.
P3G centralretryrewrite: prosecution SDKpolicy and pool fastfailure change; defense
one retryauthority simplifiesreasoning. Collision: KILL D4/D6; seed observe/gate at
actualsend while retaining SDKretryloop, rather than replaceit.
P3F/D scopedgate: prosecution onlyoutererrorcatch misses swallowedSDKwait and default
backgroundtasks can inheritcontext; defense rawsender sees sourceanswer. Collision:
SURVIVE with explicit taskregistration, monotonicsharedcooldown and budget ordering.
Cachedwait and exported/CDN paths are required combinedprebuild cases, not assumptions.
P3C independentworkers: prosecution SDK maysleepinternally and siblings keepadmitting;
defense minimalcode. Collision KILL D4; seed commonadmission rather than moreretries.
P4G newresult schema: prosecution changeshash/receipt and defaultrowsemantics; defense
uniformerrors reduceadapters. Collision KILL D1/D2/D6; seed share privateexecutiononly.
P4F/O/L readeracceptance: prosecution legacybest-effort swallows errors creatingfalse
parallelprefix; defense opt-in can explicitly failmediawhile defaultremainsbest-effort.
Collision SURVIVE with declared opted-in strictfailure and same row/order/cacheformat;
no record acceptedbeforemedia completes. Partial_data stays reader-specific.
P4C/X/U max-ID/unordered: prosecution101failed/102completed andack102 loses101;
defense outputavailablequickly. Collision KILL D2; seed completedartifacts reusable
without cursorauthority. No data schema change rescues this withinrequestedtask.
P5G broadconfig: prosecution persists tuning intohistoricalidentity, expandsworker/
profile/by-ID; defense convenience. Collision boundary, REFINE futureexplicitconsumer
requests; currentruntimeoption doesnotneedstoragechange.
P5F runtimekeyword: prosecution replay/injectedreaders mayreceiveunknowndefaultarg;
defense omitdefault1 and validateoptionbeforeI/O; pendingreplay ignores validtuning.
Collision SURVIVE; attachments disk/in-memory included, optionalprofilefetch stays
serial in parent; download_media_by_id andworkerjob protocol remain unchanged.
P5C downstreamonly: prosecution apps do notown batchblob/prefixboundary and would
needduplicateTelegramreads; defense lowerlibraryscope. Collision KILL fulfillment;
seed retain externalbenchmark/operatorchoice without relocatingimplementation.
## AssemblyS adversarial re-evaluation
Prosecution: 'smallhelper' hides sourcepolicy andSDKresource coupling; identicalclient
usedbyanotherdefaultcall evadesclaimedaccountlimit; strictopt-in errors couldsurprise.
Defense: localextent explicit, N1untouched, ownedtaskregistration + rawsendgate +
resourceaccounting cover native seams; readers keepauthority. No guaranteedaccount
cap across independent/unoptedcalls is claimed. Opt-in docs expose stricterfailure.
Collision: SURVIVE contract, rankedfirst. Required proof is combinedrealprebuild
beforeproductadoption, including cached/consumedwaits, exportcancel, CDNpolicy, duplicate
files, source-ref refreshbudget, stopduringcleanup, callbackstop and pendingreplay.
No separatearchitecture prerequisite established: componentcontract canbe implemented
in one private media unit with narrow existinghooks. Ifprebuild cannotcoverit, stop.
## Accumulator / coverage and convergence
Evaluationiteration1 screensall15 corevariants andsevenmechanismvariants through
D1–D8, retainingwholeassemblyS and futureglobal/rollingpaths. Evaluationiteration2
retestsS andalternatives against strongestgap/callback/resource counterexamples:
no newregion; rejectvariant alreadygenerated resolvesreentrantcall. Evaluationiteration3
checks N1, requestpolicy, localvsaccountscope andnewpublicsurfaces: no newregion;
no changedweights or newcandidate required. Contractdeterminations allprovided;
implementationbehavior remains experiment-gated, notfabricatedproof.
Coverage: allcriticalaxes for everycandidate; fullD1–D8 for survivors. Unexplored
liveperformance cannotselect among correctnesscontracts anddoesnotblockcontractanswer.
Mechanism independencevalidated by actualSDKsource/probe andbatch/ackimplementation,
not onlycognitiveagreement. No quarantine. AdversarialstrengthSTRONG; landscapeSTABLE
over lasttwoevaluationiterations; cleancontractSURVIVE exists; scopeclaimsbounded.
All nine failuremodes checked. TERMINATE with S; fullprebuild proofstillrequired
beforeimplementation. Structural5/5 sections andallcriticaldimensions manualPASS.
