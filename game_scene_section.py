import html
import textwrap


def build_game_hero_scene_html(
    character_mode,
    level_progress_percent,
    ready_rewards_count,
    single_boards_html,
    rider_target,
    rider_top,
    scene_height_px,
    character_icon,
    scene_tier="laptop",
    scene_density="rich",
):
    return textwrap.dedent(
        f"""
        <div class="game-hero">
            <div class="game-scene scene-tier-{html.escape(scene_tier)} scene-density-{html.escape(scene_density)}" style="--rider-start:8%; --rider-target:{rider_target:.1f}%; --rider-top:{rider_top}; --scene-height:{scene_height_px}px;">
                <div class="scene-map-header">                    
                    <div class="scene-map-ready-chip">🎁 {ready_rewards_count} Reward(s) Ready</div>
                </div>

                <div class="scene-daycycle"></div>
                <div class="scene-grain"></div>
                <div class="scene-sun"></div>
                <div class="scene-cloud-layer far">
                    <div class="scene-cloud c1"></div>
                    <div class="scene-cloud c2"></div>
                    <div class="scene-cloud c3"></div>
                </div>
                <div class="scene-cloud-layer mid">
                    <div class="scene-cloud c4"></div>
                    <div class="scene-cloud c5"></div>
                </div>
                <div class="scene-bird-lane">
                    <div class="scene-bird b1"></div>
                    <div class="scene-bird b2"></div>
                    <div class="scene-bird b3"></div>
                    <div class="scene-bird b4"></div>
                    <div class="scene-bird b5"></div>
                </div>
                <div class="scene-ridge"></div>
                <div class="scene-foreground"></div>
                <div class="scene-fence">
                    <div class="road-row single">{single_boards_html}</div>
                </div>
                <div class="game-road-layout">
                    <div class="road-strip single"></div>
                </div>

                <div class="game-rider" style="left:{rider_target:.1f}%">{character_icon}</div>

            </div>
        </div>
        """
    ).strip()
