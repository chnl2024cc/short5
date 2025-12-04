# Video Sharing Function Analysis

## Issue Found

You have **two separate functions** that do essentially the same thing:

### 1. `handleShare` in `VideoSwiper.vue`
- **Location**: Line 718-767
- **Context**: Component has video as a prop (`props.video`)
- **UI Feedback**: Uses notification system (`showShareNotification`)
- **Translation keys**: Uses `videoSwiper.*` namespace
- **Used for**: Sharing from the video swiper component

### 2. `handleShareVideo` in `liked.vue` and `profile.vue`
- **Location**: 
  - `liked.vue` line 289-320
  - `profile.vue` line 614-645
- **Context**: Pages with video lists, needs video as parameter
- **UI Feedback**: Uses simple `alert()`
- **Translation keys**: Uses `liked.*` and `profile.*` namespaces
- **Used for**: Sharing from video grid lists

## The Problem

Both functions:
- Create the same share URL format: `/?video={video.id}`
- Try Web Share API first (mobile)
- Fall back to clipboard
- Have nearly identical logic (~95% duplicate code)

**Why this happened:**
- Different contexts (component prop vs page parameter)
- Different UI feedback patterns (notification vs alert)
- Code evolved separately without consolidation

## Solution

I've created a **reusable composable** (`useShareVideo.ts`) that consolidates the logic:

### Benefits:
1. ✅ **Single source of truth** - All share logic in one place
2. ✅ **Consistent behavior** - Same share flow everywhere
3. ✅ **Easier maintenance** - Fix bugs in one place
4. ✅ **Flexible** - Supports different UI feedback patterns
5. ✅ **Type-safe** - Proper TypeScript types

### Usage Examples:

**In VideoSwiper.vue (with notification):**
```ts
const { shareVideo } = useShareVideo({
  onCopied: () => {
    showShareNotification.value = true
    setTimeout(() => {
      showShareNotification.value = false
    }, 2000)
  },
  translationPrefix: 'videoSwiper'
})

const handleShare = async () => {
  await shareVideo(props.video)
}
```

**In liked.vue / profile.vue (with alert):**
```ts
const { shareVideo } = useShareVideo({
  translationPrefix: 'liked' // or 'profile'
})

const handleShareVideo = async (video: Video) => {
  await shareVideo(video)
}
```

## Next Steps

Would you like me to:
1. ✅ Refactor all three files to use the new composable?
2. ✅ Remove the duplicate functions?
3. ✅ Ensure consistent behavior across all share buttons?

This will eliminate ~100 lines of duplicate code and make future updates much easier!
