import Phaser from "phaser";
import { AUREA_MOUNT } from "./MountCatalog";
import { characterAtlasKey, characterManifest, selectCharacterState, resolveCharacterAnimation, SpriteAnimator } from "../shared/animation";
import type { Direction } from "../shared/direction";

/** Creature-only inspection stable. Does not fake a standing hero as a seated rider. */
export class MountPreview {
  private root: HTMLDivElement;
  private sprite: Phaser.GameObjects.Sprite;
  private animator: SpriteAnimator;
  private action: string = "idle";
  private facing: Direction = "south";
  private opened: boolean = false;
  constructor(private scene: Phaser.Scene) {
    const state = selectCharacterState(characterManifest(scene, AUREA_MOUNT.id));
    this.sprite = scene.add.sprite(0, 0, characterAtlasKey(AUREA_MOUNT.id)).setScrollFactor(0).setDepth(900000).setVisible(false);
    this.animator = new SpriteAnimator(this.sprite, characterAtlasKey(AUREA_MOUNT.id), state.animations, state.stateFolder);
    this.root = document.createElement("div");
    this.root.style.cssText = "position:absolute;right:12px;top:100px;pointer-events:none;color:#f2e0b4;font:13px Arial;max-width:calc(100% - 24px)";
    this.root.innerHTML = `<button data-stable style="pointer-events:auto;background:#202731;color:#f3dfa5;border:1px solid #8d7546;padding:8px;border-radius:6px">Montaria · Áurea</button><section hidden style="pointer-events:auto;background:#151d28ee;border:1px solid #8d7546;padding:12px;border-radius:8px;width:270px;max-width:100%;box-sizing:border-box"><strong>Montaria Taurina Áurea</strong><p>Prévia sem cavaleiro. Poses sentadas dos heróis: próxima etapa.</p><label>Movimento <select data-motion>${AUREA_MOUNT.actions.map(a=>`<option value="${a}">${({idle:"Respirar",walk:"Caminhar",run:"Correr",jump:"Saltar",attack:"Atacar",hurt:"Receber golpe"})[a]}</option>`).join("")}</select></label><br><label>Direção <select data-facing>${AUREA_MOUNT.directions.map(d=>`<option>${d}</option>`).join("")}</select></label><p style="margin-bottom:0">Clique em Montaria para fechar.</p></section>`;
    document.getElementById("hud-root")!.append(this.root);
    this.root.querySelector("[data-stable]")!.addEventListener("click",()=>this.show(!this.opened));
    this.root.querySelector("[data-motion]")!.addEventListener("change",e=>this.play((e.target as HTMLSelectElement).value,this.facing));
    this.root.querySelector("[data-facing]")!.addEventListener("change",e=>this.play(this.action,(e.target as HTMLSelectElement).value as Direction));
    const hooks=window as unknown as Record<string,unknown>;
    hooks.mountPreview=(action="idle",direction:Direction="south")=>{this.show(true);this.play(action,direction);};
    hooks.mountState=()=>({opened:this.opened,action:this.action,direction:this.facing,frame:this.sprite.frame.name,riderReady:false,animations:characterManifest(scene,AUREA_MOUNT.id).states.flatMap(s=>s.animations.map(a=>({name:a.display_name||a.name,directions:a.directions.length,frames:a.frame_count}))) });
  }
  private show(open:boolean):void {this.opened=open;this.root.querySelector("section")!.hidden=!open;this.sprite.setVisible(open);if(open)this.play(this.action,this.facing);}
  private play(action:string,direction:Direction):void {
    if(!AUREA_MOUNT.actions.some(a=>a===action)||!AUREA_MOUNT.directions.some(d=>d===direction))return;
    const resolution=resolveCharacterAnimation(characterManifest(this.scene,AUREA_MOUNT.id),[action],{direction});
    if(!resolution)return;
    this.action=action;this.facing=direction;
    this.animator.setAnimationMap(resolution.animations,resolution.stateFolder);
    this.animator.setClip(resolution.clipName,direction,resolution.stateFolder);
  }
  update(delta:number):void {if(!this.opened)return;const camera=this.scene.cameras.main;this.sprite.setPosition(camera.width/2,camera.height/2);this.animator.update(delta);}
  destroy():void {this.root.remove();this.sprite.destroy();}
}
